import os
from importlib import reload


def _reload_with_db(tmp_path):
    os.environ["ASTRARPG_DB_URL"] = f"sqlite:///{tmp_path / 'migr.db'}"
    import astrarpg.config as cfg
    reload(cfg)
    import astrarpg.engine.persistence as p
    reload(p)
    return p


def test_alembic_upgrade_creates_schema(tmp_path):
    p = _reload_with_db(tmp_path)
    eng = p.get_engine()
    assert eng is not None
    p.ensure_schema(eng)
    # Introspect schema
    from sqlalchemy import inspect  # type: ignore

    insp = inspect(eng)
    tables = insp.get_table_names()
    assert "players" in tables and "alembic_version" in tables
    cols = {c["name"] for c in insp.get_columns("players")}
    assert {"id", "name", "hp", "max_hp", "attack", "defense", "gold", "inventory", "equipped_weapon", "equipped_armor", "data_version"}.issubset(cols)


def test_stamping_existing_table_and_backfill(tmp_path):
    # Create a DB with a manually created 'players' table lacking data_version
    p = _reload_with_db(tmp_path)
    eng = p.get_engine()
    assert eng is not None
    from sqlalchemy import text  # type: ignore
    with eng.begin() as conn:
        conn.execute(text(
            "CREATE TABLE players (id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, hp INTEGER NOT NULL, max_hp INTEGER NOT NULL, attack INTEGER NOT NULL, defense INTEGER NOT NULL, gold INTEGER NOT NULL, inventory TEXT NOT NULL, equipped_weapon TEXT, equipped_armor TEXT)"
        ))
    # Now ensure_schema should detect existing table, backfill data_version, and stamp head
    p.ensure_schema(eng)
    from sqlalchemy import inspect  # type: ignore
    insp = inspect(eng)
    assert "alembic_version" in insp.get_table_names()
    cols = {c["name"] for c in insp.get_columns("players")}
    assert "data_version" in cols

