import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from candle.tts.base import QuotaExceeded, RateLimited, TTSError, TTSProvider

log = logging.getLogger(__name__)


def start_of_next_month(now: datetime) -> datetime:
    first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return (first + timedelta(days=32)).replace(day=1)


class TTSRouter:
    """Try the primary provider, fall back to the secondary one.

    - TTSError: this message uses the fallback; next message tries primary again.
    - RateLimited: primary is skipped for `retry_after` seconds.
    - QuotaExceeded: primary is skipped until the 1st of next month (UTC).
    """

    def __init__(
        self,
        primary: TTSProvider | None,
        fallback: TTSProvider,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._clock = clock
        self._blocked_until: datetime | None = None

    async def synthesize(self, text: str, voice: str) -> tuple[bytes, str]:
        """Return (audio, provider name)."""
        if self._primary is not None and not self._blocked():
            try:
                return await self._primary.synthesize(text, voice), self._primary.name
            except QuotaExceeded as e:
                self._blocked_until = start_of_next_month(self._clock())
                log.warning("%s quota exhausted until %s: %s", self._primary.name, self._blocked_until.date(), e)
            except RateLimited as e:
                self._blocked_until = self._clock() + timedelta(seconds=e.retry_after)
                log.info("%s rate limited for %.0fs", self._primary.name, e.retry_after)
            except TTSError as e:
                log.info("%s failed, using %s: %s", self._primary.name, self._fallback.name, e)

        return await self._fallback.synthesize(text, voice), self._fallback.name

    def _blocked(self) -> bool:
        if self._blocked_until is None:
            return False
        if self._clock() >= self._blocked_until:
            self._blocked_until = None
            return False
        return True
