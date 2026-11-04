import pytest

from zergbot.search import ExpansionSearch


def planner():
    search = ExpansionSearch()
    search.target((100, 100), [(100, 100), (80, 80), (50, 50), (0, 0), (5, 5)], [(0, 0)])
    return search


def test_route_uses_map_candidates_and_excludes_known_home_sites():
    assert planner().route == [(100, 100), (80, 80), (50, 50)]


def test_route_requires_both_vision_and_nearby_army_before_advancing():
    search = planner()
    assert search.observe([(100, 100)], False, 0) == (100, 100)
    assert search.observe([(0, 0)], True, 4) == (100, 100)
    assert search.observe([], True, 8) == (100, 100)
    assert search.observe([(100, 100)], True, 12) == (80, 80)


def test_route_debounces_and_cycles_without_unbounded_memory():
    search = planner()
    assert search.observe([(100, 100)], True, 0) == (80, 80)
    assert search.observe([(80, 80)], True, 4) == (80, 80)
    assert search.observe([(80, 80)], True, 112) == (50, 50)
    assert search.observe([(50, 50)], True, 224) == (100, 100)
    assert len(search.route) == 3


def test_single_site_and_missing_initialization_are_safe():
    search = ExpansionSearch()
    with pytest.raises(ValueError):
        search.observe([], False, 0)
    search.target((100, 100), [], [(0, 0)])
    assert search.observe([(100, 100)], True, 0) == (100, 100)
