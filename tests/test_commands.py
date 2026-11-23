"""on_message routing and slash command registration, with fake Discord objects."""

from types import SimpleNamespace

import pytest

from candle.__main__ import Candle
from candle.cogs.commands import TTSCommands
from candle.config import load_settings
from candle.db import GuildStore


class FakeSession:
    def __init__(self):
        self.said = []
        self.last_author_id = None
        self.vc = SimpleNamespace(is_connected=lambda: True)

    def say(self, text, voice):
        self.said.append((text, voice))


def msg(guild_id, channel_id, author_id, name, content, bot=False, attachments=()):
    return SimpleNamespace(
        guild=SimpleNamespace(id=guild_id),
        channel=SimpleNamespace(id=channel_id),
        author=SimpleNamespace(id=author_id, display_name=name, bot=bot),
        clean_content=content,
        attachments=list(attachments),
    )


@pytest.fixture
async def cog(tmp_path):
    settings = load_settings({"DISCORD_TOKEN": "x"})
    store = await GuildStore.open(tmp_path / "c.db")
    await store.set_channel(1, 10)
    await store.set_channel(2, 20)
    await store.set_voice(2, "th-TH-NiwatNeural")
    bot = SimpleNamespace(settings=settings, store=store)
    c = TTSCommands(bot)
    c.sessions = {1: FakeSession(), 2: FakeSession()}
    yield c
    await store.close()


async def test_each_guild_reads_only_its_channel(cog):
    await cog.on_message(msg(1, 10, 7, "นนท์", "ห้องหนึ่ง"))
    await cog.on_message(msg(2, 20, 8, "มด", "ห้องสอง"))
    await cog.on_message(msg(1, 20, 7, "นนท์", "ผิดห้อง"))  # guild 1, guild 2's channel id
    await cog.on_message(msg(2, 99, 8, "มด", "ห้องอื่น"))

    assert cog.sessions[1].said == [("นนท์ บอกว่า ห้องหนึ่ง", "th-TH-PremwadeeNeural")]
    assert cog.sessions[2].said == [("มด บอกว่า ห้องสอง", "th-TH-NiwatNeural")]


async def test_speaker_prefix_only_when_speaker_changes(cog):
    for author, name, text in [(7, "นนท์", "หนึ่ง"), (7, "นนท์", "สอง"), (8, "มด", "สาม")]:
        await cog.on_message(msg(1, 10, author, name, text))
    assert [t for t, _ in cog.sessions[1].said] == ["นนท์ บอกว่า หนึ่ง", "สอง", "มด บอกว่า สาม"]


async def test_ignores_bots_and_skipped_messages(cog):
    await cog.on_message(msg(1, 10, 9, "bot", "ฉันเป็นบอท", bot=True))
    await cog.on_message(msg(1, 10, 7, "นนท์", "// ไม่อ่าน"))
    assert cog.sessions[1].said == []
    assert cog.sessions[1].last_author_id is None


async def test_no_session_means_silence(cog):
    del cog.sessions[1]
    await cog.on_message(msg(1, 10, 7, "นนท์", "ไม่มีใครฟัง"))  # must not raise


async def test_slash_commands_register():
    bot = Candle(load_settings({"DISCORD_TOKEN": "x"}))
    await bot.load_extension("candle.cogs.commands")
    names = sorted(c.name for c in bot.tree.get_commands())
    assert names == ["help", "join", "leave", "setup", "skip", "voice"]
    for c in bot.tree.get_commands():
        c.to_dict(bot.tree)  # raises if a payload is invalid
    await bot.unload_extension("candle.cogs.commands")


class ClosableSession(FakeSession):
    def __init__(self, vc):
        super().__init__()
        self.vc = vc
        self.closed = False

    async def close(self):
        self.closed = True


def bot_left_voice(cog, guild_voice_client):
    """Simulate the "bot left voice" event; return the guild's session."""
    vc = SimpleNamespace(is_connected=lambda: True)
    session = ClosableSession(vc)
    cog.sessions = {1: session}
    guild = SimpleNamespace(id=1, voice_client=vc if guild_voice_client == "same" else None)
    cog.bot.user = SimpleNamespace(id=999)
    cog.bot.get_guild = lambda gid: guild
    member = SimpleNamespace(id=999, guild=guild)
    return session, member


async def test_voice_reconnect_keeps_session(cog, monkeypatch):
    import asyncio

    # Patch the module the class actually runs in: unload_extension in
    # another test drops candle.cogs.commands from sys.modules.
    monkeypatch.setitem(TTSCommands._end_if_disconnected.__globals__, "RECONNECT_GRACE", 0)
    session, member = bot_left_voice(cog, guild_voice_client="same")
    await cog.on_voice_state_update(member, None, SimpleNamespace(channel=None))
    await asyncio.sleep(0.01)
    assert cog.sessions.get(1) is session
    assert not session.closed


async def test_real_disconnect_ends_session(cog, monkeypatch):
    import asyncio

    # Patch the module the class actually runs in: unload_extension in
    # another test drops candle.cogs.commands from sys.modules.
    monkeypatch.setitem(TTSCommands._end_if_disconnected.__globals__, "RECONNECT_GRACE", 0)
    session, member = bot_left_voice(cog, guild_voice_client=None)
    await cog.on_voice_state_update(member, None, SimpleNamespace(channel=None))
    await asyncio.sleep(0.01)
    assert 1 not in cog.sessions
    assert session.closed
