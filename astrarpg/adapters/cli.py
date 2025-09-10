import os
import sys

from ..engine.commands import GameState, dispatch, help_text
from ..engine.models import Player


def main() -> int:
    player_id = os.getenv("ASTRARPG_PLAYER_ID", os.getenv("USERNAME") or os.getenv("USER") or "local")
    name = os.getenv("ASTRARPG_PLAYER_NAME", player_id)
    gs = GameState(Player(id=str(player_id), name=str(name)))
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
        if done:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

