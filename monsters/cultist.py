import random
from entities import Enemy, IntentType


class Cultist(Enemy):
    def __init__(self, name="邪教徒", hp=50):
        super().__init__(name=name, hp=hp)
        self.is_first_turn = True

    def roll_intent(self):
        self.intent_base_damage = 0
        self.intent_block_amount = 0
        self.intent_powers = []

        if self.is_first_turn:
            self.intent_type = IntentType.BUFF
            self.intent_name = "黑暗仪式"
            self.intent_powers = [("仪式", 1, "self")]
            self.intent_description = "准备使用【黑暗仪式】: 获得 1 层仪式"
            self.is_first_turn = False
        else:
            self.intent_type = IntentType.ATTACK
            self.intent_name = "暗黑打击"
            self.intent_base_damage = 6
