from datetime import UTC, datetime, timedelta

import pytest

from candle.tts import QuotaExceeded, RateLimited, TTSError
from candle.tts.azure import build_ssml
from candle.tts.router import TTSRouter, start_of_next_month


class FakeProvider:
    def __init__(self, name, error=None):
        self.name = name
        self.error = error
        self.calls = 0

    async def synthesize(self, text, voice):
        self.calls += 1
        if self.error:
            raise self.error
        return f"{self.name}:{text}".encode()


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


async def test_uses_primary_when_healthy():
    router = TTSRouter(FakeProvider("azure"), FakeProvider("gtts"))
    assert await router.synthesize("hi", "v") == (b"azure:hi", "azure")


async def test_no_primary_goes_straight_to_fallback():
    router = TTSRouter(None, FakeProvider("gtts"))
    assert await router.synthesize("hi", "v") == (b"gtts:hi", "gtts")


async def test_one_off_error_falls_back_for_that_message_only():
    primary = FakeProvider("azure", TTSError("500"))
    router = TTSRouter(primary, FakeProvider("gtts"))
    assert (await router.synthesize("a", "v"))[1] == "gtts"
    primary.error = None
    assert (await router.synthesize("b", "v"))[1] == "azure"


async def test_quota_blocks_primary_until_next_month():
    clock = Clock(NOW)
    primary = FakeProvider("azure", QuotaExceeded("403"))
    router = TTSRouter(primary, FakeProvider("gtts"), clock)

    assert (await router.synthesize("a", "v"))[1] == "gtts"
    primary.error = None
    clock.now = NOW + timedelta(days=5)
    assert (await router.synthesize("b", "v"))[1] == "gtts"
    assert primary.calls == 1

    clock.now = datetime(2026, 12, 1, tzinfo=UTC)
    assert (await router.synthesize("c", "v"))[1] == "azure"


async def test_rate_limit_blocks_primary_briefly():
    clock = Clock(NOW)
    primary = FakeProvider("azure", RateLimited(30))
    router = TTSRouter(primary, FakeProvider("gtts"), clock)

    assert (await router.synthesize("a", "v"))[1] == "gtts"
    primary.error = None
    clock.now = NOW + timedelta(seconds=10)
    assert (await router.synthesize("b", "v"))[1] == "gtts"
    clock.now = NOW + timedelta(seconds=31)
    assert (await router.synthesize("c", "v"))[1] == "azure"


async def test_fallback_error_propagates():
    router = TTSRouter(FakeProvider("azure", TTSError("x")), FakeProvider("gtts", TTSError("y")))
    with pytest.raises(TTSError):
        await router.synthesize("a", "v")


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 11, 24, 12, tzinfo=UTC), datetime(2026, 12, 1, tzinfo=UTC)),
        (datetime(2026, 12, 31, 23, 59, tzinfo=UTC), datetime(2027, 1, 1, tzinfo=UTC)),
        (datetime(2027, 1, 31, tzinfo=UTC), datetime(2027, 2, 1, tzinfo=UTC)),
    ],
)
def test_start_of_next_month(now, expected):
    assert start_of_next_month(now) == expected


def test_ssml_escapes_user_text():
    ssml = build_ssml("<b>&'x'</b>", "th-TH-PremwadeeNeural")
    assert "&lt;b&gt;&amp;'x'&lt;/b&gt;" in ssml
    assert "name='th-TH-PremwadeeNeural'" in ssml or 'name="th-TH-PremwadeeNeural"' in ssml
