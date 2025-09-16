from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Item:
    name: str
    power: int = 0


@dataclass
class Player:
    id: str
    name: str
    hp: int = 10
    max_hp: int = 10
    attack: int = 2
    defense: int = 1
    gold: int = 0
    inventory: List[Item] = field(default_factory=list)
    equipped_weapon: Optional[Item] = None
    equipped_armor: Optional[Item] = None

    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass
class Monster:
    biome: str
    tier: int
    name: str = "Vermin"
    hp: int = 6
    max_hp: int = 6
    attack: int = 1
    defense: int = 0

    def is_alive(self) -> bool:
        return self.hp > 0
