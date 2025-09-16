import os
from importlib import reload


def test_save_and_load_roundtrip(tmp_path):
    # Point DB to a temp SQLite file and reload config to pick it up
    db_path = tmp_path / "astrarpg_test.db"
    os.environ["ASTRARPG_DB_URL"] = f"sqlite:///{db_path}"

    import astrarpg.config as cfg
    reload(cfg)

    import astrarpg.engine.persistence as p
    reload(p)

    from astrarpg.engine.models import Player, Item

    eng = p.get_engine()
    assert eng is not None
    p.ensure_schema(eng)

    # Create and save a player with inventory and equipped gear
    pl = Player(id="pidX", name="Hero", hp=7, max_hp=11, attack=3, defense=2, gold=42)
    pl.inventory.extend([Item(name="Scrap", power=2), Item(name="Curio", power=5)])
    pl.equipped_weapon = Item(name="Dagger", power=1)
    pl.equipped_armor = Item(name="Coat", power=1)
    p.save_player(eng, pl)

    # Load back and verify fields
    q = p.load_player(eng, "pidX")
    assert q is not None
    assert q.id == pl.id and q.name == pl.name
    assert q.hp == 7 and q.max_hp == 11
    assert q.attack == 3 and q.defense == 2 and q.gold == 42
    assert len(q.inventory) == 2 and {i.name for i in q.inventory} == {"Scrap", "Curio"}
    assert q.equipped_weapon and q.equipped_weapon.name == "Dagger"
    assert q.equipped_armor and q.equipped_armor.name == "Coat"

    # Update and re-save
    q.gold += 10
    p.save_player(eng, q)
    r = p.load_player(eng, "pidX")
    assert r and r.gold == 52

