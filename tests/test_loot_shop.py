from astrarpg.engine.loot import shop_offers, open_box, LootBox
from astrarpg.engine.models import Item


def test_shop_offers_deterministic():
    a = shop_offers("p1", cycle="2025-09-10")
    b = shop_offers("p1", cycle="2025-09-10")
    assert a == b and 1 <= len(a) <= 3


def test_open_box_deterministic():
    box = LootBox(code="iron", name="Iron Hoard", tier=2, price=0)
    r1 = open_box("p1", box, salt="x")
    r2 = open_box("p1", box, salt="x")
    assert [i.name for i in r1] == [i.name for i in r2]
    assert all(isinstance(i, Item) for i in r1)
