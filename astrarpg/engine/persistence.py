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
    """Create tables if they do not exist."""
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
            Column("inventory", Text, nullable=False),  # JSON list of {name,power}
            Column("equipped_weapon", Text, nullable=True),  # JSON or null
            Column("equipped_armor", Text, nullable=True),   # JSON or null
        )
        meta.create_all(engine)  # type: ignore[arg-type]
    except Exception:
        # Silently ignore if SQLAlchemy unavailable
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
        }
        if row is None:
            conn.execute(
                text(
                    """
                    INSERT INTO players (id, name, hp, max_hp, attack, defense, gold, inventory, equipped_weapon, equipped_armor)
                    VALUES (:id, :name, :hp, :max_hp, :attack, :defense, :gold, :inventory, :equipped_weapon, :equipped_armor)
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
                        gold=:gold, inventory=:inventory, equipped_weapon=:equipped_weapon, equipped_armor=:equipped_armor
                    WHERE id=:id
                    """
                ),
                params,
            )


def load_player(engine: object, pid: str) -> Optional[Player]:
    from sqlalchemy import text  # type: ignore

    with (engine).begin() as conn:  # type: ignore[attr-defined]
        row = conn.execute(
            text(
                "SELECT id, name, hp, max_hp, attack, defense, gold, inventory, equipped_weapon, equipped_armor FROM players WHERE id = :id"
            ),
            {"id": pid},
        ).fetchone()
        if row is None:
            return None
        inv = []
        try:
            arr = json.loads(row.inventory or "[]")  # type: ignore[attr-defined]
            for d in arr:
                inv.append(Item(name=str(d.get("name", "Unknown")), power=int(d.get("power", 0))))
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
        return p
