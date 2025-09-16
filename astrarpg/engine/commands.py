from typing import Tuple

from .models import Player, Monster, Item
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
        import datetime as _dt

        self.shop_cycle = _dt.datetime.utcnow().strftime("%Y-%m-%d")
        self.shop_cache: list | None = None
        # Bestiary discoveries
        self.discovered: set[str] = set()


def _spawn_monster(player: Player) -> Monster:
    rng = rng_for(player.id, "spawn", "wastes")
    tier = 1 + rng.randint(0, 1)
    m = Monster(biome="wastes", tier=tier, name="Carrion Rat", hp=5 + tier, max_hp=5 + tier, attack=1 + tier // 2)
    return m


def help_text() -> str:
    return (
        "Commands: help, stats, attack, fish, inv, equip, zone, map, travel, shop, buy, open, shrine, take, bestiary, sell, farm, quit"
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
            gs.discovered.add(gs.current.name)
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
        # Show inventory with simple grouping: boxes first, then items
        boxes = [it for it in gs.player.inventory if getattr(it, "name", "").startswith("[BOX] ")]
        items = [it for it in gs.player.inventory if isinstance(it, Item)]
        parts: list[str] = []
        if boxes:
            parts.append("Boxes: " + ", ".join(f"{i}) {b.name}" for i, b in enumerate(boxes, 1)))
        if items:
            parts.append(
                "Items: "
                + ", ".join(f"{i}) {it.name}(+{it.power})" for i, it in enumerate(items, 1))
            )
        if not parts:
            parts = ["(empty)"]
        # Show equipped summary
        eq = []
        if gs.player.equipped_weapon:
            eq.append(f"Weapon: {gs.player.equipped_weapon.name}(+{gs.player.equipped_weapon.power})")
        if gs.player.equipped_armor:
            eq.append(f"Armor: {gs.player.equipped_armor.name}(+{gs.player.equipped_armor.power})")
        if eq:
            parts.append("Equipped: " + ", ".join(eq))
        return ("\n".join(parts), False)
    if cmd == "bestiary":
        if not args:
            names = sorted(gs.discovered)
            if not names:
                return ("Bestiary is empty. Fight something first.", False)
            return ("Discovered: " + ", ".join(names), False)
        name = " ".join(args)
        # Optional AI flavor with fallback
        try:
            from ..genai.client import GeminiClient  # type: ignore
            from ..genai.prompts import FLAVOR_MONSTER, WORLD_NAME  # type: ignore

            gem = GeminiClient()
            prompt = FLAVOR_MONSTER.format(world=WORLD_NAME, biome="wastes", tier=1, theme=name)
            text = gem.text(prompt)
            if not text or "[flavor unavailable]" in text:
                raise RuntimeError
            return (text, False)
        except Exception:
            r = rng_for("bestiary", name)
            ep = ["bane of gutters", "slinking carrion", "ashen skulker", "rat-king's churl", "gutter shade"][r.randint(0, 4)]
            return (f"{name}\n{ep}", False)
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
    if cmd == "cycle":
        return (f"Current shop cycle: {gs.shop_cycle}", False)
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
    if cmd in {"shrine", "!shrine"}:
        # Offer 3 deterministic choices: pick a lootbox from the pool
        from .loot import shop_offers
        # Use a separate namespace so shrine differs from shop
        picks = shop_offers(gs.player.id, cycle=f"shrine:{gs.shop_cycle}")
        # Force exactly 3 by padding or trimming
        while len(picks) < 3:
            picks += shop_offers(gs.player.id, cycle=f"shrine:{gs.shop_cycle}:{len(picks)}")
        picks = picks[:3]
        gs._shrine = picks  # type: ignore[attr-defined]
        out = ["You kneel at a cracked altar. Choose:"]
        for i, b in enumerate(picks, 1):
            out.append(f" {i}) {b.name} [t{b.tier}]")
        out.append("Use 'take <n>' to claim.")
        return ("\n".join(out), False)
    if cmd in {"take", "!take"}:
        picks = getattr(gs, "_shrine", None)
        if not picks:
            return ("No shrine choices active. Use 'shrine' first.", False)
        if not args:
            return ("Take which? Use 'take <n>'.", False)
        try:
            idx = int(args[0]) - 1
        except Exception:
            return ("Invalid selection.", False)
        if idx < 0 or idx >= len(picks):
            return ("No such offering.", False)
        chosen = picks[idx]
        # Grant chosen lootbox
        gs.player.inventory.append(
            type("_LootItem", (object,), {"name": f"[BOX] {chosen.name}", "_box_code": chosen.code, "_box_tier": chosen.tier})()
        )
        gs._shrine = None  # type: ignore[attr-defined]
        return (f"The altar hums. You receive a {chosen.name}.", False)
    if cmd in {"equip", "!equip"}:
        # Usage: equip <n> [weapon|armor] OR equip [weapon|armor] <n>
        if not args:
            return ("Usage: equip <n> [weapon|armor]", False)
        slot: str = "weapon"
        idx_str: str | None = None
        a0 = args[0].lower()
        if a0 in {"weapon", "w", "armor", "a"}:
            slot = "weapon" if a0.startswith("w") else "armor"
            if len(args) < 2:
                return ("Usage: equip <n> [weapon|armor]", False)
            idx_str = args[1]
        else:
            idx_str = args[0]
            if len(args) >= 2 and args[1].lower() in {"weapon", "w", "armor", "a"}:
                slot = "weapon" if args[1].lower().startswith("w") else "armor"
        try:
            idx = int(idx_str) - 1  # type: ignore[arg-type]
        except Exception:
            return ("Invalid selection.", False)
        items = [it for it in gs.player.inventory if isinstance(it, Item)]
        if not items:
            return ("No equippable items in your inventory.", False)
        if idx < 0 or idx >= len(items):
            return ("No such item.", False)
        chosen = items[idx]
        # Move currently equipped item (if any) back to inventory and adjust stats
        if slot == "weapon":
            if gs.player.equipped_weapon is chosen:
                return ("Already equipped.", False)
            if gs.player.equipped_weapon is not None:
                gs.player.attack -= gs.player.equipped_weapon.power
                gs.player.inventory.append(gs.player.equipped_weapon)
            gs.player.equipped_weapon = chosen
            gs.player.attack += chosen.power
        else:
            if gs.player.equipped_armor is chosen:
                return ("Already equipped.", False)
            if gs.player.equipped_armor is not None:
                gs.player.defense -= gs.player.equipped_armor.power
                gs.player.inventory.append(gs.player.equipped_armor)
            gs.player.equipped_armor = chosen
            gs.player.defense += chosen.power
        # Remove the selected item instance from inventory
        for i, it in enumerate(gs.player.inventory):
            if it is chosen:
                gs.player.inventory.pop(i)
                break
        return (f"Equipped {chosen.name}(+{chosen.power}) as {slot}.", False)
    if cmd in {"sell", "!sell"}:
        # Usage: sell <n>  (sells nth item from 'Items' list)
        if not args:
            return ("Usage: sell <n>", False)
        try:
            idx = int(args[0]) - 1
        except Exception:
            return ("Invalid selection.", False)
        items = [it for it in gs.player.inventory if isinstance(it, Item)]
        if idx < 0 or idx >= len(items):
            return ("No such item.", False)
        chosen = items[idx]
        price = max(1, int(chosen.power))
        # Remove chosen instance from inventory
        for i, it in enumerate(gs.player.inventory):
            if it is chosen:
                gs.player.inventory.pop(i)
                break
        gs.player.gold += price
        return (f"Sold {chosen.name} for {price}g.", False)
    if cmd in {"farm", "!farm"}:
        return ("That system is not implemented yet in this scaffold.", False)
    return ("Unknown command. Try 'help'.", False)
