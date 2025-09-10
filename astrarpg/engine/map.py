from dataclasses import dataclass
from typing import Tuple, List

from .generation import rng_for


DIRS = {
    "n": (0, -1),
    "s": (0, 1),
    "w": (-1, 0),
    "e": (1, 0),
}


BIOMES = [
    "wastes",
    "fen",
    "heath",
    "moor",
    "ashwood",
    "saltplain",
]

ADJ = ["ashen", "bleak", "sodden", "howling", "salt-bitten", "ironbound"]
NOUN = ["barrow", "copse", "ridge", "sink", "trace", "glen", "cut"]


@dataclass(frozen=True)
class Zone:
    x: int
    y: int
    name: str
    biome: str
    tier: int


def bounds(size: Tuple[int, int]) -> Tuple[int, int, int, int]:
    w, h = size
    return (0, 0, w - 1, h - 1)


def in_bounds(x: int, y: int, size: Tuple[int, int]) -> bool:
    x0, y0, x1, y1 = 0, 0, size[0] - 1, size[1] - 1
    return x0 <= x <= x1 and y0 <= y <= y1


def zone_for(pid: str, x: int, y: int) -> Zone:
    r = rng_for("zone", pid, x, y)
    biome = BIOMES[r.randint(0, len(BIOMES) - 1)]
    tier = 1 + (abs(x) + abs(y)) // 2
    name = f"{ADJ[r.randint(0, len(ADJ) - 1)]} {NOUN[r.randint(0, len(NOUN) - 1)]}"
    return Zone(x=x, y=y, name=name, biome=biome, tier=tier)


def render_map(pid: str, size: Tuple[int, int], pos: Tuple[int, int]) -> str:
    w, h = size
    px, py = pos
    cx, cy = w // 2, h // 2
    # We render a viewport centered on current pos if possible
    # For simplicity on a fixed grid map, the viewport is the whole map
    rows: List[str] = []
    for y in range(h):
        cells: List[str] = []
        for x in range(w):
            gx, gy = x, y
            if (gx, gy) == (px, py):
                cells.append("@")
            else:
                z = zone_for(pid, gx - cx, gy - cy)
                # biome hint by first letter
                mark = z.biome[0]
                cells.append(mark)
        rows.append("".join(cells))
    legend = "(" + ", ".join(b[0] + ":" + b for b in BIOMES) + ")"
    return "\n".join(rows) + "\n" + legend

