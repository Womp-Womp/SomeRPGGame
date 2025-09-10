from astrarpg.engine.commands import GameState, dispatch
from astrarpg.engine.models import Player


def make_state():
    return GameState(Player(id="test", name="Tester"))


def run(cmd: str):
    gs = make_state()
    msg, done = dispatch(gs, cmd)
    return msg, done


def test_help_and_stats():
    msg, done = run("help")
    assert "Commands" in msg and not done
    msg, done = run("stats")
    assert "HP" in msg and not done


def test_attack_and_fish():
    msg, done = run("attack")
    assert "strike" in msg.lower() and not done
    msg, done = run("fish")
    assert "You cast into black water" in msg


def test_unknown():
    msg, done = run("unknowncmd")
    assert "Unknown" in msg and not done


def test_zone_map_travel():
    gs = make_state()
    msg, done = dispatch(gs, "zone")
    assert "Exits" in msg and not done
    msg, done = dispatch(gs, "map")
    assert "@" in msg and not done
    # Move north and check position changed visually
    msg_before, _ = dispatch(gs, "map")
    _, _ = dispatch(gs, "travel n")
    msg_after, _ = dispatch(gs, "map")
    assert msg_before != msg_after


def test_shop_buy_open():
    gs = make_state()
    gs.player.gold = 1000
    msg, done = dispatch(gs, "shop")
    assert "Shop offers" in msg and not done
    # Attempt to buy first offer
    msg, _ = dispatch(gs, "buy 1")
    assert "Purchased" in msg
    # Opening first lootbox in inventory listing
    msg, _ = dispatch(gs, "open 1")
    assert "clicks open" in msg
