import asyncio
import io

from gtts import gTTS
from gtts.tts import gTTSError

from candle.tts.base import TTSError


class GoogleTranslateTTS:
    """gTTS: free, one Thai voice, used when Azure is unavailable."""

    name = "gtts"

    async def synthesize(self, text: str, voice: str) -> bytes:
        return await asyncio.to_thread(self._synthesize, text)

    @staticmethod
    def _synthesize(text: str) -> bytes:
        buf = io.BytesIO()
        try:
            gTTS(text, lang="th").write_to_fp(buf)
        except (gTTSError, AssertionError) as e:
            raise TTSError(f"gtts failed: {e}") from e
        return buf.getvalue()
