from action import Action
from action import ActionTypes
from stats import Stats

import random


class ActionAttack(Action):
    def __init__(self, owner):
        super().__init__(owner)

        self.name = "Attack"
        self.type = ActionTypes.SINGLE_TARGET

    def do_action(self, targets):
        if super().do_action(targets):
            return

        target = targets[0]
        min_damage = self.owner.stats.get_stat(Stats.MIN_DAMAGE)
        max_damage = self.owner.stats.get_stat(Stats.MAX_DAMAGE)
        damage_roll = random.randrange(min_damage, max_damage + 1)
        damage = max(damage_roll - target.stats.get_stat(Stats.DEFENCE), 0)
        target.stats.remove_stat(Stats.CURRENT_HEALTH, damage)

        return f"{self.name} did {damage} damage to {target.name}"
