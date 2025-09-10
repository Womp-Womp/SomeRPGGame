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
