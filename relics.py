# relics.py

class Relic:
    """遗物基类：定义所有可能的事件钩子"""
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

    # ==========================
    # 生命周期钩子 (默认什么都不做)
    # ==========================
    def on_combat_start(self, engine, player, enemy):
        pass

    def on_combat_end(self, player):
        pass

    def on_turn_start(self, engine, player):
        pass

    def on_card_play(self, engine, player, card_data):
        pass


# ==========================================
# 具体遗物实现
# ==========================================

class BurningBlood(Relic):
    """铁甲卫士初始遗物：战斗结束回血"""
    def __init__(self):
        super().__init__("burning_blood", "燃烧之血", "在战斗结束时，回复 6 点生命。")

    def on_combat_end(self, player):
        heal_amount = 6
        player.hp = min(player.max_hp, player.hp + heal_amount)
        print(f"\n  🩸 【{self.name}】发光了！你回复了 {heal_amount} 点生命。")


class Vajra(Relic):
    """经典数值遗物：开局加力量"""
    def __init__(self):
        super().__init__("vajra", "金刚杵", "在每场战斗开始时，获得 1 点力量。")

    def on_combat_start(self, engine, player, enemy):
        # 完美复用我们现有的动作队列系统
        from engine import ApplyPowerAction
        print(f"\n  ✨ 【{self.name}】发光了！")
        engine.action_queue.add_bottom(ApplyPowerAction(player, "力量", 1))