from astrarpg.engine.models import Player, Monster
from astrarpg.engine.combat import player_attack, monster_attack


def test_player_and_monster_exchange():
    p = Player(id="p1", name="Wanderer", attack=3, defense=1, hp=10, max_hp=10)
    m = Monster(biome="wastes", tier=1, name="Carrion Rat", hp=6, max_hp=6, attack=2, defense=0)
    out1 = player_attack(p, m)
    assert isinstance(out1, str) and len(out1) > 0
    # After a hit, monster HP should be <= original
    assert 0 <= m.hp <= m.max_hp
    if m.is_alive():
        out2 = monster_attack(p, m)
        assert isinstance(out2, str)
        assert 0 <= p.hp <= p.max_hp
