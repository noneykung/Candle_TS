import asyncio
import contextlib
import io
import logging
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import discord

from candle.tts.base import TTSError
from candle.tts.router import TTSRouter

log = logging.getLogger(__name__)

QUEUE_MAX = 10
DAVE_READY_TIMEOUT = 10.0  # seconds to wait for voice E2EE before playing anyway


@dataclass(frozen=True)
class Speech:
    text: str
    voice: str


@dataclass(frozen=True)
class Sound:
    path: Path


Item = Speech | Sound


class GuildPlayer:
    """Plays items one at a time. When full, the oldest waiting item is dropped."""

    def __init__(self, play: Callable[[Item], Awaitable[None]], maxlen: int = QUEUE_MAX) -> None:
        self._play = play
        self._items: deque[Item] = deque(maxlen=maxlen)
        self._wake = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    def put(self, item: Item) -> None:
        self._items.append(item)  # deque(maxlen) drops from the left
        self._wake.set()

    def pending(self) -> int:
        return len(self._items)

    async def close(self) -> None:
        self._items.clear()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _run(self) -> None:
        while True:
            while not self._items:
                self._wake.clear()
                await self._wake.wait()
            item = self._items.popleft()
            try:
                await self._play(item)
            except Exception:
                log.exception("playback failed")


class VoiceSession:
    """The bot's voice connection in one guild: queue, playback, who spoke last."""

    def __init__(self, vc: discord.VoiceClient, router: TTSRouter) -> None:
        self.vc = vc
        self._router = router
        self.last_author_id: int | None = None
        self.leave_task: asyncio.Task[None] | None = None
        self.player = GuildPlayer(self._play)
        self.player.start()

    def say(self, text: str, voice: str) -> None:
        self.player.put(Speech(text, voice))

    def sound(self, path: Path) -> None:
        self.player.put(Sound(path))

    def skip(self) -> bool:
        if self.vc.is_playing():
            self.vc.stop()  # ends the current item; the player moves on
            return True
        return False

    async def close(self) -> None:
        if self.leave_task is not None:
            self.leave_task.cancel()
        await self.player.close()
        if self.vc.is_connected():
            await self.vc.disconnect()

    async def _play(self, item: Item) -> None:
        if isinstance(item, Speech):
            try:
                audio, provider = await self._router.synthesize(item.text, item.voice)
            except TTSError as e:
                log.warning("guild=%s tts failed: %s", self.vc.guild.id, e)
                return
            log.info("guild=%s len=%d provider=%s", self.vc.guild.id, len(item.text), provider)
            source = discord.FFmpegOpusAudio(io.BytesIO(audio), pipe=True)
        else:
            source = discord.FFmpegOpusAudio(str(item.path))

        if not self.vc.is_connected():
            source.cleanup()
            return

        loop = asyncio.get_running_loop()
        done = loop.create_future()

        def after(error: Exception | None) -> None:
            if error:
                log.warning("guild=%s player error: %s", self.vc.guild.id, error)
            loop.call_soon_threadsafe(lambda: done.done() or done.set_result(None))

        await self._wait_for_dave()
        self.vc.play(source, after=after)
        await done

    async def _wait_for_dave(self) -> None:
        """Hold playback until the DAVE (E2EE) session is ready.

        discord.py 2.7 sends frames unencrypted while the MLS handshake is
        still running, and clients in an E2EE call drop them, so audio
        played right after connecting is silent. Uses private discord.py
        state (`_connection`); recheck on library upgrades.
        """
        conn = self.vc._connection
        if conn.dave_protocol_version == 0 or conn.can_encrypt:
            return
        loop = asyncio.get_running_loop()
        start = loop.time()
        while loop.time() - start < DAVE_READY_TIMEOUT:
            if conn.dave_protocol_version == 0 or conn.can_encrypt:
                break
            await asyncio.sleep(0.1)
        log.info(
            "guild=%s dave_version=%s dave_ready=%s waited=%.1fs",
            self.vc.guild.id,
            conn.dave_protocol_version,
            conn.can_encrypt,
            loop.time() - start,
        )
