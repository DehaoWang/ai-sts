class Power:
    """所有状态的基类 (等同于源码中的 AbstractPower)"""

    def __init__(self, owner, amount):
        self.owner = owner  # 状态的持有者 (Entity)
        self.amount = amount  # 状态的层数
        self.name = "未知状态"
        self.is_debuff = False  # 是否为负面状态
        self.priority = 99

    # 【新增魔法方法】：当系统尝试 print 这个对象时，返回易读的字符串
    def __repr__(self):
        return f"{self.amount}层{self.name}"

    def at_damage_give(self, damage):
        """可用于力量加成、虚弱减伤等"""
        return damage

    def at_damage_receive(self, damage):
        """当持有者作为防御方时触发"""
        return damage

    def on_turn_end(self):
        pass


# ==========================================
# 具体状态实现
# ==========================================
class VulnerablePower(Power):
    def __init__(self, owner, amount):
        super().__init__(owner, amount)
        self.name = "易伤"
        self.is_debuff = True
        self.priority = 10

    def at_damage_receive(self, damage):
        return damage * 1.5

    def on_turn_end(self):
        # 易伤的自我衰减逻辑
        self.amount -= 1
        print(f"  ⏳ {self.owner.name} 的 【{self.name}】 衰减了 1 层。")


# 👇 【完善力量逻辑】
class StrengthPower(Power):
    def __init__(self, owner, amount):
        super().__init__(owner, amount)
        self.name = "力量"
        self.is_debuff = False
        self.priority = 0

    def at_damage_give(self, damage):
        # 力量的核心法则：直接将层数加到基础伤害上
        return damage + self.amount

    # 力量不需要 on_turn_end，因为它不会随回合自然衰减


class RitualPower(Power):
    def __init__(self, owner, amount):
        super().__init__(owner, amount)
        self.name = "仪式"
        self.is_debuff = False

    def on_turn_end(self):
        # 核心机制：回合结束时，将自身的层数转化为力量
        # (为了防止循环导入，这里直接操作 owner 的 powers 字典)
        if "Strength" in self.owner.powers:
            self.owner.powers["Strength"].amount += self.amount
        else:
            # 如果身上没有力量对象，则实例化一个赋给它
            self.owner.powers["Strength"] = StrengthPower(self.owner, self.amount)

        print(f"  🦅 CAW CAW！【{self.name}】共鸣！{self.owner.name} 自动增长了 {self.amount} 点力量！")


class WeakPower(Power):
    def __init__(self, owner, amount):
        super().__init__(owner, amount)
        self.name = "虚弱"
        self.is_debuff = True
        self.priority = 10

    def at_damage_give(self, damage):
        # 虚弱的本职工作：将持有者【造成的伤害】降低 25% (向下取整)
        return damage * 0.75

    def on_turn_end(self):
        # 虚弱是一种随回合衰减的状态
        self.amount -= 1
        print(f"  ⏳ {self.owner.name} 的 【{self.name}】 衰减了 1 层。")
