from .models import Player, Monster
from .generation import rng_for


def player_attack(player: Player, monster: Monster) -> str:
    rng = rng_for(player.id, "combat", monster.name)
    swing = max(0, player.attack - monster.defense + rng.randint(0, 1))
    monster.hp = max(0, monster.hp - swing)
    if monster.hp == 0:
        return f"You strike for {swing}. The {monster.name} falls."
    return f"You strike for {swing}. {monster.name} has {monster.hp}/{monster.max_hp}."


def monster_attack(player: Player, monster: Monster) -> str:
    rng = rng_for("monster", monster.name, player.id)
    swing = max(0, monster.attack - player.defense + rng.randint(0, 1))
    player.hp = max(0, player.hp - swing)
    if player.hp == 0:
        return f"{monster.name} hits for {swing}. You fall."
    return f"{monster.name} hits for {swing}. You have {player.hp}/{player.max_hp}."

