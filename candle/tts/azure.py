from xml.sax.saxutils import escape, quoteattr

import aiohttp

from candle.tts.base import QuotaExceeded, RateLimited, TTSError

# Thai neural voices offered by /voice. Check against the live list when
# changing: GET https://<region>.tts.speech.microsoft.com/cognitiveservices/voices/list
THAI_VOICES = {
    "th-TH-PremwadeeNeural": "เปรมวดี (หญิง)",
    "th-TH-AcharaNeural": "อัจฉรา (หญิง)",
    "th-TH-NiwatNeural": "นิวัฒน์ (ชาย)",
}

DEFAULT_RETRY_AFTER = 60.0  # F0 allows about 20 requests per minute


def build_ssml(text: str, voice: str) -> str:
    return (
        "<speak version='1.0' xml:lang='th-TH'>"
        f"<voice name={quoteattr(voice)}>{escape(text)}</voice>"
        "</speak>"
    )


class AzureTTS:
    name = "azure"

    def __init__(self, session: aiohttp.ClientSession, key: str, region: str) -> None:
        self._session = session
        self._key = key
        self._url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

    async def synthesize(self, text: str, voice: str) -> bytes:
        headers = {
            "Ocp-Apim-Subscription-Key": self._key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "ogg-48khz-16bit-mono-opus",
            "User-Agent": "candle-ts",
        }
        try:
            async with self._session.post(
                self._url,
                data=build_ssml(text, voice).encode(),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
                detail = (await resp.text())[:200]
                if resp.status == 429:
                    raise RateLimited(_retry_after(resp.headers.get("Retry-After")), detail)
                if resp.status in (401, 403):
                    # F0 answers 403 once the monthly quota is used up; a bad key
                    # (401) also means there is no point retrying this month.
                    raise QuotaExceeded(f"azure {resp.status}: {detail}")
                raise TTSError(f"azure {resp.status}: {detail}")
        except (aiohttp.ClientError, TimeoutError) as e:
            raise TTSError(f"azure request failed: {e!r}") from e


def _retry_after(header: str | None) -> float:
    try:
        return max(1.0, float(header)) if header else DEFAULT_RETRY_AFTER
    except ValueError:
        return DEFAULT_RETRY_AFTER
