from typing import Tuple

from .models import Player, Monster
from .combat import player_attack, monster_attack
from .generation import rng_for


class GameState:
    def __init__(self, player: Player):
        self.player = player
        self.current: Monster | None = None
        # Map state: fixed viewport 7x5, start at center
        self.map_size = (7, 5)
        self.pos = (self.map_size[0] // 2, self.map_size[1] // 2)
        self.visited: set[tuple[int, int]] = {self.pos}
        # Shop state: cache offers per cycle tag
        self.shop_cycle = "daily"
        self.shop_cache: list | None = None


def _spawn_monster(player: Player) -> Monster:
    rng = rng_for(player.id, "spawn", "wastes")
    tier = 1 + rng.randint(0, 1)
    m = Monster(biome="wastes", tier=tier, name="Carrion Rat", hp=5 + tier, max_hp=5 + tier, attack=1 + tier // 2)
    return m


def help_text() -> str:
    return (
        "Commands: help, stats, attack, fish, inv, equip, zone, map, travel, shop, buy, open, sell, farm, quit"
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
    if cmd in {"shop", "!shop"}:
        from .loot import shop_offers

        if gs.shop_cache is None:
            gs.shop_cache = shop_offers(gs.player.id, gs.shop_cycle)
        lines = [f"Shop offers ({gs.shop_cycle}):"]
        for i, box in enumerate(gs.shop_cache, start=1):
            lines.append(f" {i}) {box.name} [t{box.tier}] - {box.price}g")
        if len(lines) == 1:
            lines.append(" (no offers)")
        return ("\n".join(lines), False)
    if cmd in {"zone", "!zone"}:
        from .map import zone_for

        w, h = gs.map_size
        cx, cy = w // 2, h // 2
        x, y = gs.pos
        zx, zy = x - cx, y - cy
        z = zone_for(gs.player.id, zx, zy)
        exits = []
        from .map import DIRS, in_bounds

        for k, (dx, dy) in DIRS.items():
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny, gs.map_size):
                exits.append(k)
        return (f"{z.name} [{z.biome} t{z.tier}] Exits: {', '.join(exits) if exits else '(none)'}", False)
    if cmd in {"map", "!map"}:
        from .map import render_map

        return (render_map(gs.player.id, gs.map_size, gs.pos), False)
    if cmd in {"travel", "!travel"}:
        if not args:
            return ("Travel where? Try: travel n|s|e|w", False)
        direction = args[0].lower()[0]
        from .map import DIRS, in_bounds

        if direction not in DIRS:
            return ("Unknown direction. Use n/s/e/w.", False)
        dx, dy = DIRS[direction]
        x, y = gs.pos
        nx, ny = x + dx, y + dy
        if not in_bounds(nx, ny, gs.map_size):
            return ("You cannot travel further that way.", False)
        gs.pos = (nx, ny)
        gs.visited.add(gs.pos)
        return ("You pick your way through the waste...", False)
    if cmd in {"buy", "!buy"}:
        if gs.shop_cache is None:
            return ("View the shop first with 'shop'.", False)
        if not args:
            return ("Buy which? Use 'buy <number>'.", False)
        try:
            idx = int(args[0]) - 1
        except Exception:
            return ("Invalid selection.", False)
        if idx < 0 or idx >= len(gs.shop_cache):
            return ("That offer does not exist.", False)
        box = gs.shop_cache[idx]
        if gs.player.gold < box.price:
            return ("You cannot afford that.", False)
        gs.player.gold -= box.price
        # Represent lootboxes in inventory as items with a marker
        gs.player.inventory.append(
            type("_LootItem", (object,), {"name": f"[BOX] {box.name}", "_box_code": box.code, "_box_tier": box.tier})()
        )
        return (f"Purchased {box.name}.", False)
    if cmd in {"open", "!open"}:
        if not args:
            return ("Open which? Use 'open <number>' from your inventory list of boxes.", False)
        # Find nth lootbox-like item in inventory
        try:
            idx = int(args[0]) - 1
        except Exception:
            return ("Invalid selection.", False)
        boxes = [it for it in gs.player.inventory if getattr(it, "name", "").startswith("[BOX] ")]
        if idx < 0 or idx >= len(boxes):
            return ("No such lootbox.", False)
        box_item = boxes[idx]
        from .loot import LootBox, open_box

        box = LootBox(code=getattr(box_item, "_box_code"), name=getattr(box_item, "name")[7:], tier=getattr(box_item, "_box_tier"), price=0)
        rewards = open_box(gs.player.id, box, salt="open")
        # Remove that specific lootbox item
        for i, it in enumerate(gs.player.inventory):
            if it is box_item:
                gs.player.inventory.pop(i)
                break
        gs.player.inventory.extend(rewards)
        names = ", ".join(f"{it.name}(+{it.power})" for it in rewards)
        return (f"The {box.name} clicks open: {names}", False)
    if cmd in {"equip", "!equip", "sell", "!sell", "farm", "!farm"}:
        return ("That system is not implemented yet in this scaffold.", False)
    return ("Unknown command. Try 'help'.", False)
