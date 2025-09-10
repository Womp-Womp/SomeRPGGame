from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .generation import rng_for
from .models import Item, Player


@dataclass(frozen=True)
class LootBox:
    code: str
    name: str
    tier: int
    price: int


# A small pool to start; expand easily
POOL: List[LootBox] = [
    LootBox("copper", "Copper Cache", 1, 5),
    LootBox("tin", "Tin Trove", 1, 9),
    LootBox("iron", "Iron Hoard", 2, 20),
    LootBox("silver", "Silver Reliquary", 2, 35),
    LootBox("gold", "Gilded Reliquary", 3, 60),
    LootBox("obs", "Obsidian Reliquary", 3, 90),
    LootBox("myth", "Mythril Reliquary", 4, 140),
    LootBox("eld", "Elder Reliquary", 5, 220),
    LootBox("abyss", "Abyssal Reliquary", 6, 360),
    LootBox("void", "Void Reliquary", 7, 580),
    LootBox("star", "Starborn Reliquary", 8, 900),
    LootBox("apex", "Apex Reliquary", 9, 1400),
]


def shop_offers(pid: str, cycle: str = "daily") -> List[LootBox]:
    """Deterministic 1-3 offers from the pool, based on player and cycle.

    cycle may be a date string (YYYY-MM-DD) or any caller-supplied tag.
    """
    r = rng_for("shop", pid, cycle)
    count = 1 + r.randint(0, 2)  # 1..3
    # Select distinct boxes
    idxs = list(range(len(POOL)))
    picks: List[LootBox] = []
    for _ in range(count):
        i = r.randint(0, len(idxs) - 1)
        picks.append(POOL[idxs.pop(i)])
    # Sort by price for stable display order
    picks.sort(key=lambda b: b.price)
    return picks


def open_box(pid: str, box: LootBox, salt: str = "") -> List[Item]:
    """Deterministic rewards based on player, box, and salt."""
    r = rng_for("loot", pid, box.code, box.tier, salt)
    # Scale absurdly over time: simple exponential-ish growth by tier
    base = 1 + box.tier
    pow_mult = 2 ** max(0, box.tier - 1)
    # Roll 1-3 items
    k = 1 + r.randint(0, 2)
    items: List[Item] = []
    for _ in range(k):
        roll = r.randint(0, 99)
        if roll < 60:
            items.append(Item(name="Scrap", power=base * pow_mult))
        elif roll < 90:
            items.append(Item(name="Curio", power=base * pow_mult * 3))
        else:
            items.append(Item(name="Relic", power=base * pow_mult * 7))
    return items

