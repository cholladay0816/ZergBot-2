import pytest

from zergbot.threat_inference import DamageEvidence, SourceBounds, TerrainCell, infer_region


def test_unknown_source_is_not_identified_from_damage_or_one_candidate():
    result = infer_region(DamageEvidence((0, 0), 10), [TerrainCell((4, 0), 10, False)])
    assert result.source_type is None and not result.source_confirmed and not result.exhaustive
    assert len(result.cells) == 1


def test_range_includes_splash_radii_projectile_and_movement_uncertainty():
    evidence = DamageEvidence(
        (0, 0), 10, observation_delay=0.2, victim_speed_bound=2, source_confirmed=True
    )
    profile = SourceBounds("confirmed_test_type", 10, 1, 2, 0.8, 3, False)
    result = infer_region(
        evidence, [TerrainCell((17, 0), 0, False), TerrainCell((19, 0), 0, False)], profile
    )
    assert result.radius == 18
    assert [c.position for c in result.cells] == [(17, 0)]


def test_current_visibility_does_not_prove_source_absent_at_damage_time():
    evidence = DamageEvidence((0, 0), 10, source_confirmed=True)
    profile = SourceBounds("known_nonhidden", 10, 0, 0, 0, 0, False)
    cells = [
        TerrainCell((1, 0), 0, True),
        TerrainCell((2, 0), 0, True, visible_throughout_interval=True),
    ]
    assert len(infer_region(evidence, cells, profile).cells) == 1
    hidden = SourceBounds("possibly_hidden", 10, 0, 0, 0, 0, True)
    assert len(infer_region(evidence, cells, hidden).cells) == 2


def test_unknown_type_does_not_use_a_hypothesis_range_as_exclusive_bound():
    profile = SourceBounds("unconfirmed_tank", 5, 0, 0, 0, 0, False)
    result = infer_region(DamageEvidence((0, 0), 1), [TerrainCell((12, 0), 0, False)], profile)
    assert result.cells and result.source_type is None


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_uncertainty_rejected(value):
    with pytest.raises(ValueError):
        infer_region(DamageEvidence((0, 0), 1), [], search_radius=value)
