from astrarpg.engine.commands import GameState, dispatch
from astrarpg.engine.models import Player, Item


def make_state():
    gs = GameState(Player(id="t", name="Tester"))
    # Seed inventory with a couple items
    gs.player.inventory.extend([
        Item(name="Scrap", power=2),
        Item(name="Curio", power=3),
    ])
    return gs


def test_equip_weapon_and_armor():
    gs = make_state()
    base_atk, base_def = gs.player.attack, gs.player.defense
    # Equip first item as weapon
    msg, done = dispatch(gs, "equip 1 weapon")
    assert "Equipped" in msg and not done
    assert gs.player.attack == base_atk + 2
    # Add an armor item and equip as armor
    gs.player.inventory.append(Item(name="Relic", power=5))
    msg, done = dispatch(gs, "equip 2 armor")  # 2nd item in current Items list
    assert "Equipped" in msg and not done
    assert gs.player.defense == base_def + 5


def test_sell_item_by_index():
    gs = make_state()
    gold_before = gs.player.gold
    msg, done = dispatch(gs, "sell 2")
    assert "Sold" in msg and not done
    assert gs.player.gold == gold_before + 3
    # Inventory should have one remaining item (we seeded two)
    remaining_items = [it for it in gs.player.inventory if isinstance(it, Item)]
    assert len(remaining_items) == 1

