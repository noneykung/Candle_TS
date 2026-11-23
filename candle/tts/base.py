from typing import Protocol


class TTSError(Exception):
    """A provider failed for this one request (timeout, 5xx, bad response)."""


class QuotaExceeded(TTSError):
    """The provider's monthly quota is used up; stop calling it until reset."""


class TTSProvider(Protocol):
    name: str

    async def synthesize(self, text: str, voice: str) -> bytes:
        """Return encoded audio (any format ffmpeg can read) for `text`.

        Raises TTSError on failure, QuotaExceeded when the quota is gone.
        """
        ...
