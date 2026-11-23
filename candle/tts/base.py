from typing import Protocol


class TTSError(Exception):
    """A provider failed for this one request (timeout, 5xx, bad response)."""


class RateLimited(TTSError):
    """The provider asked us to back off for a while (HTTP 429)."""

    def __init__(self, retry_after: float, message: str = "rate limited") -> None:
        super().__init__(message)
        self.retry_after = retry_after


class QuotaExceeded(TTSError):
    """The provider's monthly quota is used up; stop calling it until reset."""


class TTSProvider(Protocol):
    name: str

    async def synthesize(self, text: str, voice: str) -> bytes:
        """Return encoded audio (any format ffmpeg can read) for `text`.

        Raises TTSError on failure, QuotaExceeded when the quota is gone.
        """
        ...
