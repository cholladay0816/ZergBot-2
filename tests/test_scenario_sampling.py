from zergbot.scenarios import MeasuredBot


def test_sampling_survives_offset_frames_and_remains_bounded():
    bot = MeasuredBot(None, None)
    frames = [0, 1, 5, 9, 13, 17, 21, 25, 29, 33]
    assert [f for f in frames if bot.sample_due("tank", f, 16)] == [0, 17, 33]
    assert bot.sample_due("construction", 33, 112)
    assert not bot.sample_due("construction", 100, 112)
    assert bot.sample_due("construction", 149, 112)


def test_worker_order_serialization_uses_actual_ability_enum():
    import json
    from types import SimpleNamespace

    from sc2.ids.ability_id import AbilityId
    from sc2.position import Point2

    from zergbot.scenarios import observed_order

    order = SimpleNamespace(ability=SimpleNamespace(id=AbilityId.HARVEST_GATHER), target=42)
    assert json.loads(json.dumps(observed_order(order))) == {
        "ability": AbilityId.HARVEST_GATHER.value,
        "target": 42,
    }
    order.target = Point2((1, 2))
    assert observed_order(order)["target"] is None


def test_both_scenario_setups_finish_before_either_player_steps():
    import asyncio
    from types import SimpleNamespace

    async def run():
        barrier = asyncio.Barrier(2)
        first, second = MeasuredBot(None, None, barrier), MeasuredBot(None, None, barrier)
        first.state = second.state = SimpleNamespace(game_loop=0)
        waiting = asyncio.create_task(first.setup_ready())
        await asyncio.sleep(0)
        assert not waiting.done()
        await second.setup_ready()
        await waiting
        assert first.events == [{"frame": 0, "kind": "setup_ready"}]
        assert second.events == first.events

    asyncio.run(run())
