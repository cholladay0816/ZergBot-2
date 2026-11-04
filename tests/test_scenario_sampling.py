from zergbot.scenarios import MeasuredBot


def test_sampling_survives_offset_frames_and_remains_bounded():
    bot = MeasuredBot(None, None)
    frames = [0, 1, 5, 9, 13, 17, 21, 25, 29, 33]
    assert [f for f in frames if bot.sample_due("tank", f, 16)] == [0, 17, 33]
    assert bot.sample_due("construction", 33, 112)
    assert not bot.sample_due("construction", 100, 112)
    assert bot.sample_due("construction", 149, 112)
