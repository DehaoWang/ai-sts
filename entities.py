from enum import Enum
from utils import calculate_final_damage


# --- 1. 意图类型枚举 ---
class IntentType(Enum):
    ATTACK = "攻击"
    DEFEND = "防御"
    BUFF = "强化"
    DEBUFF = "削弱"
    ATTACK_DEFEND = "攻防一体"
    UNKNOWN = "未知"


# --- 2. 基础实体类 (补充了 powers 和 block) ---
class Entity:
    def __init__(self, name, hp):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.block = 0
        self.powers = {}

    def clear_block(self):
        self.block = 0

    def tick_powers(self):
        """向所有持有的状态广播：回合结束了！"""
        powers_to_remove = []

        for power_id, power_obj in list(self.powers.items()):
            # 触发状态自己的回合结束逻辑
            power_obj.on_turn_end()

            # 如果层数归零，标记移除
            if power_obj.amount <= 0:
                powers_to_remove.append(power_id)

        # 清除已失效的状态
        for p_id in powers_to_remove:
            removed_name = self.powers[p_id].name
            del self.powers[p_id]
            print(f"  ✨ {self.name} 的 【{removed_name}】 状态已完全解除！")


# --- 3. 怪物基类 ---
class Enemy(Entity):
    def __init__(self, name, hp):
        super().__init__(name, hp)
        self.intent_type = IntentType.UNKNOWN
        self.intent_name = ""
        self.intent_base_damage = 0  # 永远不变的基底值 (如: 11)
        self.intent_damage = 0  # 经过属性放大后的真实面板值 (如: 14)
        self.intent_block_amount = 0
        self.intent_powers = []  # 格式例如：[("力量", 3, "self"), ("虚弱", 1, "enemy")]
        self.intent_description = ""

    def apply_powers(self, target):
        # 1. 先重置面板数值，准备重新计算
        self.intent_damage = calculate_final_damage(self.intent_base_damage, self, target)
        # 2. 🌟 动态意图文本生成器 (String Builder)
        fragments = []

        # 检查伤害组件
        if self.intent_base_damage > 0:
            fragments.append(f"造成 {self.intent_damage} 点伤害")

        # 检查格挡组件
        if self.intent_block_amount > 0:
            fragments.append(f"获得 {self.intent_block_amount} 点格挡")

        # 检查状态组件
        for power_name, amount, power_target in self.intent_powers:
            if power_target == "self":
                fragments.append(f"获得 {amount} 层【{power_name}】")
            else:
                fragments.append(f"给予目标 {amount} 层【{power_name}】")

        # 3. 拼接最终文案
        if fragments:
            # 用“，并”连接最后一个元素，前面的用逗号连接，让语感更自然
            if len(fragments) > 1:
                desc = "，".join(fragments[:-1]) + f"，并{fragments[-1]}"
            else:
                desc = fragments[0]
            self.intent_description = f"准备使用【{self.intent_name}】: {desc}"
        else:
            self.intent_description = f"准备使用【{self.intent_name}】: 未知行动"




        # """核心机制：重新计算并固化当前的真实意图数值 (等同于源码的 applyPowers)"""
        # if self.intent_base_damage > 0:
        #
        #     # 【核心】：结结实实地固化到属性上！
        #     self.intent_damage = calculate_final_damage(self.intent_base_damage, self, target)
        #
        #
        #     # 更新文本描述 (直接修改自身属性，不搞动态生成)
        #     if self.intent_type == IntentType.ATTACK:
        #         self.intent_description = f"准备使用【{self.intent_name}】: 造成 {self.intent_damage} 点伤害"
        #     elif self.intent_type == IntentType.DEBUFF:
        #         self.intent_description = f"准备使用【{self.intent_name}】: 造成 {self.intent_damage} 点伤害并给予易伤"
        #     else:
        #         self.intent_description = f"准备使用【{self.intent_name}】: 造成 {self.intent_damage} 点伤害并获得格挡"

        print(f"⚠️ 敌方当前意图: {self.intent_description}")

    def roll_intent(self):
        """每个回合开始时调用，决定这回合要干什么"""
        raise NotImplementedError("具体的怪物必须实现自己的 AI 决策逻辑")

    def execute_intent(self, engine, target):
        from engine import DamageAction, ApplyPowerAction, GainBlockAction
        print(f"\n👾 {self.name} 执行行动！")

        # 1. 结算伤害组件
        if self.intent_base_damage > 0:
            engine.action_queue.add_bottom(DamageAction(self, target, self.intent_base_damage))

        # 2. 结算格挡组件
        if self.intent_block_amount > 0:
            engine.action_queue.add_bottom(GainBlockAction(self, self.intent_block_amount))

        # 3. 结算状态组件
        for power_name, amount, power_target in self.intent_powers:
            actual_target = self if power_target == "self" else target
            # 这里统一用中文别名去触发引擎
            engine.action_queue.add_bottom(ApplyPowerAction(actual_target, power_name, amount))
