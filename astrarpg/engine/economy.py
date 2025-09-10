from .models import Player, Item


def buy(player: Player, item: Item, price: int) -> str:
    if player.gold < price:
        return "You cannot afford that."
    player.gold -= price
    player.inventory.append(item)
    return f"Purchased {item.name} for {price}g."


def sell(player: Player, item_name: str, price: int) -> str:
    for i, it in enumerate(player.inventory):
        if it.name.lower() == item_name.lower():
            player.inventory.pop(i)
            player.gold += price
            return f"Sold {it.name} for {price}g."
    return "You don't have that."

