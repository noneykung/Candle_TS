import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from candle.config import Settings, load_settings

log = logging.getLogger("candle")

# Cogs are added here as Phase 2 lands them, e.g. "candle.cogs.commands".
EXTENSIONS: tuple[str, ...] = ()


class Candle(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # privileged: enable in the Developer Portal
        intents.voice_states = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.settings = settings

    async def setup_hook(self) -> None:
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

    async def on_ready(self) -> None:
        log.info("logged in as %s (%s), in %d guilds", self.user, self.user.id, len(self.guilds))
        await self.change_presence(
            activity=discord.Game(name="อยู่ห่างไกลมันเหงาใจ อยากชื่นใจต้องอยู่ใกล้กัน~")
        )


def main() -> None:
    load_dotenv()
    settings = load_settings()
    discord.utils.setup_logging(level=logging.INFO)
    if settings.azure_speech_key is None:
        log.warning("AZURE_SPEECH_KEY not set; every message will use gTTS")
    Candle(settings).run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
