import hashlib
import random
from typing import Any


def make_seed(*parts: Any) -> int:
    s = ":".join(map(str, parts))
    return int(hashlib.sha256(s.encode()).hexdigest()[:16], 16)


def rng_for(*parts: Any) -> random.Random:
    return random.Random(make_seed(*parts))

