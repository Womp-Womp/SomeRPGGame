from astrarpg.engine.generation import make_seed, rng_for


def test_make_seed_deterministic():
    s1 = make_seed("player", 1, "combat")
    s2 = make_seed("player", 1, "combat")
    assert s1 == s2


def test_rng_for_stable_sequence():
    r1 = rng_for("a", 42, "b")
    r2 = rng_for("a", 42, "b")
    seq1 = [r1.randint(0, 10) for _ in range(5)]
    seq2 = [r2.randint(0, 10) for _ in range(5)]
    assert seq1 == seq2
