import random
from entities import Enemy, IntentType


class JawWorm(Enemy):
    def __init__(self, name="大颚冲", hp=40):
        super().__init__(name=name, hp=hp)
        self.is_first_turn = True

    def roll_intent(self):
        # 每次宣告意图前，先清空上回合的残留数据
        self.intent_base_damage = 0
        self.intent_block_amount = 0
        self.intent_powers = []

        roll = random.random()
        if roll < 0.25:
            self.set_intent_chomp()
        elif roll < 0.5:
            self.set_intent_bellow()
        elif roll < 0.75:
            self.set_intent_bash()
        else:
            self.set_intent_thrash()

    def set_intent_chomp(self):
        self.intent_type = IntentType.ATTACK
        self.intent_name = "咬"
        self.intent_base_damage = 11

    def set_intent_bellow(self):
        self.intent_type = IntentType.BUFF
        self.intent_name = "咆哮"
        self.intent_powers = [("力量", 3, "self")]
        self.intent_block_amount = 6
        # self.intent_description = "准备使用【咆哮】: 获得 3 点力量 和 6 点格挡"

    def set_intent_thrash(self):
        self.intent_type = IntentType.ATTACK_DEFEND
        self.intent_name = "痛击"
        self.intent_base_damage = 7
        self.intent_block_amount = 5

    def set_intent_bash(self):
        self.intent_type = IntentType.DEBUFF
        self.intent_name = "BASH"
        self.intent_base_damage = 8
        self.intent_powers = [("易伤", 2, "target")]
