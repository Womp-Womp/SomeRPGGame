import os
import sys

from ..engine.commands import GameState, dispatch, help_text
from ..engine.models import Player


def _load_or_create_state(pid: str, name: str) -> GameState:
    # Try persistence if available
    try:
        from ..engine.persistence import get_engine, ensure_schema, load_player, save_player  # type: ignore

        eng = get_engine()
        if eng is not None:
            ensure_schema(eng)
            maybe = load_player(eng, pid)
            if maybe is not None:
                return GameState(maybe)
            # Not found: create new and save baseline
            gs = GameState(Player(id=str(pid), name=str(name)))
            save_player(eng, gs.player)
            return gs
    except Exception:
        pass
    return GameState(Player(id=str(pid), name=str(name)))


def main() -> int:
    player_id = os.getenv("ASTRARPG_PLAYER_ID", os.getenv("USERNAME") or os.getenv("USER") or "local")
    name = os.getenv("ASTRARPG_PLAYER_NAME", player_id)
    gs = _load_or_create_state(str(player_id), str(name))
    print("The Abysm of Karth welcomes you. Type 'help' to begin.\n")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nFarewell, wanderer.")
            return 0
        if not raw:
            continue
        msg, done = dispatch(gs, raw)
        print(msg)
        # Best-effort autosave
        try:
            from ..engine.persistence import get_engine, save_player  # type: ignore

            eng = get_engine()
            if eng is not None:
                save_player(eng, gs.player)
        except Exception:
            pass
        if done:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
