import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    discord_token: str
    azure_speech_key: str | None
    azure_region: str
    dev_guild_id: int | None
    db_path: Path
    default_voice: str


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    def get(name: str) -> str | None:
        value = env.get(name, "").strip()
        return value or None

    token = get("DISCORD_TOKEN")
    if token is None:
        raise ConfigError("DISCORD_TOKEN is not set (copy .env.example to .env)")

    guild = get("DEV_GUILD_ID")
    if guild is not None and not guild.isdigit():
        raise ConfigError(f"DEV_GUILD_ID must be a number, got {guild!r}")

    return Settings(
        discord_token=token,
        azure_speech_key=get("AZURE_SPEECH_KEY"),
        azure_region=get("AZURE_REGION") or "southeastasia",
        dev_guild_id=int(guild) if guild else None,
        db_path=Path(get("DB_PATH") or "data/candle.db"),
        default_voice=get("DEFAULT_VOICE") or "th-TH-PremwadeeNeural",
    )
