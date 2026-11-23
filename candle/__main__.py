import logging
import os

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from candle.config import Settings, load_settings
from candle.db import GuildStore
from candle.tts.azure import AzureTTS
from candle.tts.gtts_provider import GoogleTranslateTTS
from candle.tts.router import TTSRouter

log = logging.getLogger("candle")

EXTENSIONS = ("candle.cogs.commands",)


class Candle(commands.Bot):
    store: GuildStore
    router: TTSRouter

    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # privileged: enable in the Developer Portal
        intents.voice_states = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.settings = settings
        self._http_session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self.store = await GuildStore.open(self.settings.db_path)
        self._http_session = aiohttp.ClientSession()
        azure = (
            AzureTTS(self._http_session, self.settings.azure_speech_key, self.settings.azure_region)
            if self.settings.azure_speech_key
            else None
        )
        self.router = TTSRouter(azure, GoogleTranslateTTS())

        for ext in EXTENSIONS:
            await self.load_extension(ext)

        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("synced %d commands to dev guild %s", len(synced), guild.id)
        else:
            synced = await self.tree.sync()
            log.info("synced %d commands globally", len(synced))

    async def close(self) -> None:
        await super().close()  # unloads cogs, which leaves voice channels
        if self._http_session is not None:
            await self._http_session.close()
        if hasattr(self, "store"):
            await self.store.close()

    async def on_ready(self) -> None:
        assert self.user is not None
        log.info("logged in as %s (%s), in %d guilds", self.user, self.user.id, len(self.guilds))
        await self.change_presence(
            activity=discord.Game(name="อยู่ห่างไกลมันเหงาใจ อยากชื่นใจต้องอยู่ใกล้กัน~")
        )


class _VoiceOnly(logging.Filter):
    """Keep voice/DAVE debug lines only.

    Allow-list by message prefix: main-gateway events (GUILD_CREATE,
    MESSAGE_CREATE) carry member lists and message content and must never
    pass, even though some contain the word "voice".
    """

    PREFIXES = (
        "voice websocket",
        "sending voice websocket",
        "mls ",
        "set mls",
        "preparing for dave",
        "executing dave",
        "received supported encryption",
        "selected the voice protocol",
        "sending ip discovery",
        "received ip discovery",
        "detected ip",
        "received secret key",
        "connecting to voice socket",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno > logging.DEBUG:
            return True
        msg = record.getMessage().lower()
        if "token" in msg or "secret_key" in msg:
            return False
        return msg.startswith(self.PREFIXES)


def _enable_voice_debug() -> None:
    for name in ("discord.gateway", "discord.voice_state", "discord.voice_client"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addFilter(_VoiceOnly())


def main() -> None:
    load_dotenv()
    settings = load_settings()
    discord.utils.setup_logging(level=logging.INFO)
    if os.environ.get("VOICE_DEBUG") == "1":
        _enable_voice_debug()
    if settings.azure_speech_key is None:
        log.warning("AZURE_SPEECH_KEY not set; every message will use gTTS")
    Candle(settings).run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
