from candle.db import GuildSettings, GuildStore


async def test_unknown_guild_has_empty_settings(tmp_path):
    store = await GuildStore.open(tmp_path / "c.db")
    assert store.get(1) == GuildSettings(1)
    await store.close()


async def test_settings_are_per_guild(tmp_path):
    store = await GuildStore.open(tmp_path / "c.db")
    await store.set_channel(1, 100)
    await store.set_channel(2, 200)
    await store.set_voice(1, "th-TH-NiwatNeural")

    assert store.get(1) == GuildSettings(1, 100, "th-TH-NiwatNeural")
    assert store.get(2) == GuildSettings(2, 200, None)
    await store.close()


async def test_settings_survive_reopen(tmp_path):
    path = tmp_path / "nested" / "c.db"
    store = await GuildStore.open(path)
    await store.set_channel(1, 100)
    await store.set_voice(1, "th-TH-AcharaNeural")
    await store.close()

    store = await GuildStore.open(path)
    assert store.get(1) == GuildSettings(1, 100, "th-TH-AcharaNeural")
    await store.close()


async def test_changing_channel_keeps_voice(tmp_path):
    store = await GuildStore.open(tmp_path / "c.db")
    await store.set_voice(1, "th-TH-NiwatNeural")
    await store.set_channel(1, 300)
    assert store.get(1).voice == "th-TH-NiwatNeural"
    await store.close()
