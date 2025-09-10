from astrarpg.engine.commands import GameState, dispatch
from astrarpg.engine.models import Player


def make_state():
    return GameState(Player(id="t", name="T"))


def test_bestiary_unlock_and_lookup():
    gs = make_state()
    # Attack to encounter and unlock
    dispatch(gs, "attack")
    msg, _ = dispatch(gs, "bestiary")
    assert "Discovered:" in msg or "empty" in msg.lower() is False
    # Lookup by name should return 2-line flavor (fallback ok)
    name = sorted(gs.discovered)[0] if gs.discovered else "Carrion Rat"
    msg, _ = dispatch(gs, f"bestiary {name}")
    assert name in msg


def test_shrine_and_take():
    gs = make_state()
    msg, _ = dispatch(gs, "shrine")
    assert "Choose:" in msg
    msg, _ = dispatch(gs, "take 2")
    assert "receive a" in msg
