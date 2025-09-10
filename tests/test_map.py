from astrarpg.engine.map import zone_for, render_map, in_bounds


def test_zone_determinism():
    z1 = zone_for("pid", 0, 0)
    z2 = zone_for("pid", 0, 0)
    assert z1 == z2
    assert z1.name and z1.biome


def test_render_map_contains_player():
    out = render_map("pid", (7, 5), (3, 2))
    assert "@" in out
    assert out.count("@") == 1


def test_in_bounds_edges():
    size = (7, 5)
    assert in_bounds(0, 0, size)
    assert in_bounds(6, 4, size)
    assert not in_bounds(-1, 0, size)
    assert not in_bounds(7, 4, size)
