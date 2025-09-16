from __future__ import annotations

import json
from typing import Optional

from ..config import DB_URL
from .models import Player, Item


def get_engine() -> Optional[object]:
    try:
        from sqlalchemy import create_engine  # type: ignore

        return create_engine(DB_URL)
    except Exception:
        # SQLAlchemy not installed or misconfigured; return None to indicate unavailable
        return None


def ensure_schema(engine: object) -> None:
    """Ensure DB schema via Alembic, with graceful fallback and stamping.

    - If Alembic is available, attempt to upgrade to head.
    - If DB has tables created outside Alembic, stamp head and backfill missing columns.
    - If Alembic is unavailable, create tables minimally.
    """
    # Paths
    import os as _os
    import pathlib as _pl
    root = _pl.Path(__file__).resolve().parents[2]  # .../SomeRPGGame
    alembic_ini = str(root / "alembic.ini")
    alembic_dir = str(root / "alembic")

    try:
        from sqlalchemy import inspect, text  # type: ignore
        from alembic import command  # type: ignore
        from alembic.config import Config  # type: ignore

        insp = inspect(engine)  # type: ignore[arg-type]
        tables = set(insp.get_table_names())
        has_alembic = "alembic_version" in tables
        has_players = "players" in tables

        # Helper to build config bound to our files and dynamic URL
        def _acfg() -> Config:
            cfg = Config(alembic_ini)
            cfg.set_main_option("script_location", alembic_dir)
            cfg.set_main_option("sqlalchemy.url", DB_URL)
            return cfg

        if not has_alembic:
            if has_players:
                # Backfill missing columns (e.g., data_version) prior to stamping
                cols = {c["name"] for c in insp.get_columns("players")}
                if "data_version" not in cols:
                    # Add with default
                    with (engine).begin() as conn:  # type: ignore[attr-defined]
                        conn.execute(text("ALTER TABLE players ADD COLUMN data_version INTEGER NOT NULL DEFAULT 1"))
                # Stamp to head without running migrations
                try:
                    command.stamp(_acfg(), "head")
                except Exception:
                    pass
            else:
                # Fresh DB: run migrations
                try:
                    command.upgrade(_acfg(), "head")
                except Exception:
                    pass
        else:
            # Normal path: upgrade to head
            try:
                command.upgrade(_acfg(), "head")
            except Exception:
                pass
    except Exception:
        # Fallback: minimal create_all if SQLAlchemy present
        try:
            from sqlalchemy import MetaData, Table, Column, String, Integer, Text  # type: ignore

            meta = MetaData()
            Table(
                "players",
                meta,
                Column("id", String, primary_key=True),
                Column("name", String, nullable=False),
                Column("hp", Integer, nullable=False),
                Column("max_hp", Integer, nullable=False),
                Column("attack", Integer, nullable=False),
                Column("defense", Integer, nullable=False),
                Column("gold", Integer, nullable=False),
                Column("inventory", Text, nullable=False),
                Column("equipped_weapon", Text, nullable=True),
                Column("equipped_armor", Text, nullable=True),
                Column("data_version", Integer, nullable=False),
            )
            meta.create_all(engine)  # type: ignore[arg-type]
        except Exception:
            pass
    # Ensure an alembic_version row exists even if Alembic was unavailable
    try:
        from sqlalchemy import inspect, text  # type: ignore

        insp = inspect(engine)  # type: ignore[arg-type]
        tables = set(insp.get_table_names())
        if "alembic_version" not in tables:
            with (engine).begin() as conn:  # type: ignore[attr-defined]
                conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
                conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0001_initial')"))
        # Ensure players.data_version exists
        if "players" in tables:
            cols = {c["name"] for c in insp.get_columns("players")}
            if "data_version" not in cols:
                with (engine).begin() as conn:  # type: ignore[attr-defined]
                    conn.execute(text("ALTER TABLE players ADD COLUMN data_version INTEGER NOT NULL DEFAULT 1"))
    except Exception:
        pass


def _item_to_json(it: Optional[Item]) -> Optional[str]:
    if it is None:
        return None
    return json.dumps({"name": it.name, "power": it.power})


def _item_from_json(s: Optional[str]) -> Optional[Item]:
    if not s:
        return None
    try:
        d = json.loads(s)
        return Item(name=str(d.get("name", "Unknown")), power=int(d.get("power", 0)))
    except Exception:
        return None


DATA_VERSION = 1


def save_player(engine: object, player: Player) -> None:
    """Insert or update a player row."""
    from sqlalchemy import text  # type: ignore

    inv_json = json.dumps([{"name": it.name, "power": it.power} for it in player.inventory])
    ew = _item_to_json(player.equipped_weapon)
    ea = _item_to_json(player.equipped_armor)
    with (engine).begin() as conn:  # type: ignore[attr-defined]
        row = conn.execute(text("SELECT id FROM players WHERE id = :id"), {"id": player.id}).fetchone()
        params = {
            "id": player.id,
            "name": player.name,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "attack": player.attack,
            "defense": player.defense,
            "gold": player.gold,
            "inventory": inv_json,
            "equipped_weapon": ew,
            "equipped_armor": ea,
            "data_version": DATA_VERSION,
        }
        if row is None:
            conn.execute(
                text(
                    """
                    INSERT INTO players (id, name, hp, max_hp, attack, defense, gold, inventory, equipped_weapon, equipped_armor, data_version)
                    VALUES (:id, :name, :hp, :max_hp, :attack, :defense, :gold, :inventory, :equipped_weapon, :equipped_armor, :data_version)
                    """
                ),
                params,
            )
        else:
            conn.execute(
                text(
                    """
                    UPDATE players
                    SET name=:name, hp=:hp, max_hp=:max_hp, attack=:attack, defense=:defense,
                        gold=:gold, inventory=:inventory, equipped_weapon=:equipped_weapon, equipped_armor=:equipped_armor,
                        data_version=:data_version
                    WHERE id=:id
                    """
                ),
                params,
            )


def _coerce_item_dict(d: object) -> Optional[Item]:
    if not isinstance(d, dict):
        return None
    name = d.get("name")
    power = d.get("power")
    try:
        name_s = str(name)
        power_i = int(power)
    except Exception:
        return None
    if not name_s:
        return None
    return Item(name=name_s, power=power_i)


def load_player(engine: object, pid: str) -> Optional[Player]:
    from sqlalchemy import text  # type: ignore

    with (engine).begin() as conn:  # type: ignore[attr-defined]
        row = conn.execute(
            text(
                "SELECT id, name, hp, max_hp, attack, defense, gold, inventory, equipped_weapon, equipped_armor, "
                "COALESCE(data_version, 1) AS data_version FROM players WHERE id = :id"
            ),
            {"id": pid},
        ).fetchone()
        if row is None:
            return None
        inv: list[Item] = []
        try:
            raw = row.inventory or "[]"  # type: ignore[attr-defined]
            arr = json.loads(raw)
            if isinstance(arr, list):
                for d in arr:
                    it = _coerce_item_dict(d)
                    if it is not None:
                        inv.append(it)
        except Exception:
            inv = []
        p = Player(
            id=row.id,  # type: ignore[attr-defined]
            name=row.name,  # type: ignore[attr-defined]
            hp=int(row.hp),  # type: ignore[attr-defined]
            max_hp=int(row.max_hp),  # type: ignore[attr-defined]
            attack=int(row.attack),  # type: ignore[attr-defined]
            defense=int(row.defense),  # type: ignore[attr-defined]
            gold=int(row.gold),  # type: ignore[attr-defined]
            inventory=inv,
        )
        p.equipped_weapon = _item_from_json(row.equipped_weapon)  # type: ignore[attr-defined]
        p.equipped_armor = _item_from_json(row.equipped_armor)  # type: ignore[attr-defined]
        # Potential future per-row migrations based on data_version
        _ = int(getattr(row, "data_version", 1))  # type: ignore[arg-type]
        return p
