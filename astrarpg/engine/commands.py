from typing import Tuple

from .models import Player, Monster
from .combat import player_attack, monster_attack
from .generation import rng_for


class GameState:
    def __init__(self, player: Player):
        self.player = player
        self.current: Monster | None = None


def _spawn_monster(player: Player) -> Monster:
    rng = rng_for(player.id, "spawn", "wastes")
    tier = 1 + rng.randint(0, 1)
    m = Monster(biome="wastes", tier=tier, name="Carrion Rat", hp=5 + tier, max_hp=5 + tier, attack=1 + tier // 2)
    return m


def help_text() -> str:
    return (
        "Commands: help, stats, attack, fish, inv, equip, zone, travel, buy, sell, farm, quit"
    )


def dispatch(gs: GameState, raw: str) -> Tuple[str, bool]:
    cmd, *args = raw.strip().split()
    cmd = cmd.lower()
    if cmd in {"quit", "exit"}:
        return ("Farewell, wanderer.", True)
    if cmd in {"help", "!help"}:
        return (help_text(), False)
    if cmd in {"stats", "!stats"}:
        p = gs.player
        return (f"{p.name}: HP {p.hp}/{p.max_hp}, ATK {p.attack}, DEF {p.defense}, GOLD {p.gold}", False)
    if cmd in {"attack", "!attack"}:
        if gs.current is None or not gs.current.is_alive():
            gs.current = _spawn_monster(gs.player)
        m = gs.current
        out1 = player_attack(gs.player, m)
        if m.is_alive():
            out2 = monster_attack(gs.player, m)
            return (out1 + "\n" + out2, False)
        return (out1, False)
    if cmd in {"fish", "!fish"}:
        rng = rng_for(gs.player.id, "fish")
        found = ["a bone hook", "a tangle of hair", "a pale minnow", "nothing"][rng.randint(0, 3)]
        return (f"You cast into black water and pull up {found}.", False)
    if cmd in {"inv", "!inv"}:
        items = ", ".join(it.name for it in gs.player.inventory) or "(empty)"
        return (f"Inventory: {items}", False)
    if cmd in {"equip", "!equip", "zone", "!zone", "travel", "!travel", "buy", "!buy", "sell", "!sell", "farm", "!farm"}:
        return ("That system is not implemented yet in this scaffold.", False)
    return ("Unknown command. Try 'help'.", False)

