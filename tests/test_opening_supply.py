from zergbot.config import BotConfig
from zergbot.economy import needs_overlord


def test_starting_drone_can_spend_before_thirteen_supply_overlord():
    config = BotConfig(opening_supply=True)
    assert not needs_overlord(2, 14, 0, 1, config)
    assert needs_overlord(1, 14, 0, 1, config)
    assert not needs_overlord(1, 14, 1, 1, config)
    assert needs_overlord(2, 14, 0, 1, BotConfig())


def test_opening_rule_releases_to_normal_multi_base_supply_and_caps():
    config = BotConfig(opening_supply=True)
    assert not needs_overlord(3, 22, 0, 1, config)
    assert needs_overlord(1, 22, 0, 1, config)
    assert needs_overlord(3, 22, 0, 2, config)
    assert needs_overlord(3, 30, 0, 1, config)
    assert not needs_overlord(0, 200, 0, 1, config)
