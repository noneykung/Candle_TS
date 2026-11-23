from dataclasses import dataclass, replace
from pathlib import Path

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id       INTEGER PRIMARY KEY,
    tts_channel_id INTEGER,
    voice          TEXT
)
"""


@dataclass(frozen=True)
class GuildSettings:
    guild_id: int
    tts_channel_id: int | None = None
    voice: str | None = None


class GuildStore:
    """Per-server settings in SQLite, cached in memory.

    on_message reads settings for every message, so reads come from the
    cache; the DB is only touched on startup and when a setting changes.
    """

    def __init__(self, db: aiosqlite.Connection, cache: dict[int, GuildSettings]) -> None:
        self._db = db
        self._cache = cache

    @classmethod
    async def open(cls, path: Path | str) -> "GuildStore":
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(path)
        await db.execute(_SCHEMA)
        await db.commit()
        async with db.execute("SELECT guild_id, tts_channel_id, voice FROM guild_settings") as cur:
            cache = {row[0]: GuildSettings(*row) async for row in cur}
        return cls(db, cache)

    async def close(self) -> None:
        await self._db.close()

    def get(self, guild_id: int) -> GuildSettings:
        return self._cache.get(guild_id) or GuildSettings(guild_id)

    async def set_channel(self, guild_id: int, channel_id: int | None) -> GuildSettings:
        return await self._save(replace(self.get(guild_id), tts_channel_id=channel_id))

    async def set_voice(self, guild_id: int, voice: str) -> GuildSettings:
        return await self._save(replace(self.get(guild_id), voice=voice))

    async def _save(self, s: GuildSettings) -> GuildSettings:
        await self._db.execute(
            "INSERT INTO guild_settings (guild_id, tts_channel_id, voice) VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET tts_channel_id = excluded.tts_channel_id, voice = excluded.voice",
            (s.guild_id, s.tts_channel_id, s.voice),
        )
        await self._db.commit()
        self._cache[s.guild_id] = s
        return s
