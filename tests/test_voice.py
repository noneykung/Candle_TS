import asyncio

from candle.voice import GuildPlayer, Speech


class Recorder:
    def __init__(self, fail_on=()):
        self.played = []
        self.fail_on = set(fail_on)
        self.gate = asyncio.Event()
        self.gate.set()

    async def __call__(self, item):
        await self.gate.wait()
        if item.text in self.fail_on:
            raise RuntimeError("boom")
        self.played.append(item.text)


async def drain(player, recorder, n):
    for _ in range(100):
        if len(recorder.played) >= n and player.pending() == 0:
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"played {recorder.played}")


async def test_plays_in_order():
    rec = Recorder()
    player = GuildPlayer(rec)
    player.start()
    for t in "abc":
        player.put(Speech(t, "v"))
    await drain(player, rec, 3)
    assert rec.played == ["a", "b", "c"]
    await player.close()


async def test_full_queue_drops_oldest_waiting():
    rec = Recorder()
    rec.gate.clear()  # hold playback so items pile up
    player = GuildPlayer(rec, maxlen=3)
    player.start()

    player.put(Speech("first", "v"))
    await asyncio.sleep(0.01)  # "first" is now being played, not waiting
    for t in ["a", "b", "c", "d"]:
        player.put(Speech(t, "v"))
    assert player.pending() == 3

    rec.gate.set()
    await drain(player, rec, 4)
    assert rec.played == ["first", "b", "c", "d"]
    await player.close()


async def test_failed_item_does_not_stop_player():
    rec = Recorder(fail_on={"bad"})
    player = GuildPlayer(rec)
    player.start()
    for t in ["a", "bad", "c"]:
        player.put(Speech(t, "v"))
    await drain(player, rec, 2)
    assert rec.played == ["a", "c"]
    await player.close()


async def test_wakes_after_idle():
    rec = Recorder()
    player = GuildPlayer(rec)
    player.start()
    await asyncio.sleep(0.02)
    player.put(Speech("late", "v"))
    await drain(player, rec, 1)
    assert rec.played == ["late"]
    await player.close()
