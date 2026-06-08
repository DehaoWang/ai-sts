from collections import deque
from utils import calculate_final_damage
from powers import VulnerablePower, StrengthPower, RitualPower, WeakPower

# 建立一个支持别名映射的注册表
POWER_REGISTRY = {
    "Vulnerable": VulnerablePower,
    "Strength": StrengthPower,
    "Ritual": RitualPower,
    "Weak": WeakPower,  # 👈 英文 ID

    "易伤": VulnerablePower,
    "力量": StrengthPower,
    "仪式": RitualPower,
    "虚弱": WeakPower  # 👈 中文别名
}


# ==========================================
# 2. 健壮的动作队列调度器 (Action Queue)
# ==========================================
class ActionQueue:
    def __init__(self):
        self.queue = deque()
        # 【防递归锁】：防止遗物连锁触发导致的无限递归死循环
        self.is_resolving = False

    def add_bottom(self, action):
        """常规动作，加入队尾"""
        self.queue.append(action)

    def add_top(self, action):
        """紧急动作，插入队头（用于插队结算，如反伤机制）"""
        self.queue.appendleft(action)

    def clear(self):
        """强制清空队列（用于战斗结束或关键实体死亡时打断后续动作）"""
        self.queue.clear()

    def resolve_all(self, engine):
        """安全结算流水线"""
        # 如果已经在结算循环中，直接返回，让最外层循环继续处理，防止爆栈
        if self.is_resolving:
            return

        self.is_resolving = True

        try:
            while self.queue:
                current_action = self.queue.popleft()

                if current_action is None:
                    continue

                # 引擎将自身作为上下文 (Context) 传给动作
                current_action.execute(engine)
                current_action.is_done = True

        except Exception as e:
            print(f"❌ 动作队列发生严重崩溃: {e}")
            self.clear()  # 发生异常时清空队列，切断错误链
            raise

        finally:
            # 无论是否报错，强制释放锁
            self.is_resolving = False


# ==========================================
# 3. 游戏主引擎枢纽 (Game Engine)
# ==========================================
class GameEngine:
    def __init__(self, deck_manager=None):
        self.action_queue = ActionQueue()
        # 引擎应当拥有整个战局的上下文，比如牌库管理器
        self.deck_manager = deck_manager
        self.current_enemies = []  # 当前战斗中的敌人列表

    def play_card(self, card_data, source, target):
        print(f"\n▶️ 玩家打出了卡牌: 【{card_data['name']}】 (消耗 {card_data.get('cost', 0)} 费)")

        # 1. 解析 JSON 数据，生成对应的 Action 对象
        for effect in card_data['effects']:
            action_type = effect['action']
            amount = effect.get('amount', 0)  # 默认数值为0，避免 KeyError
            target_type = effect.get('target', 'none')  # 默认目标为敌人

            if action_type == "Damage":
                if target_type == "enemy":
                    # 获取 JSON 里的 amount 和 target，实例化动作并塞入队列
                    action = DamageAction(source, target, amount)
                    self.action_queue.add_bottom(action)

                elif target_type == "all_enemies":
                    for enemy in self.current_enemies:
                        action = DamageAction(source, enemy, amount)
                        self.action_queue.add_bottom(action)

            elif action_type == "Block":
                action = GainBlockAction(source, amount)
                self.action_queue.add_bottom(action)

            elif action_type == "Draw":
                action = DrawCardAction(amount)
                self.action_queue.add_bottom(action)

            elif action_type == "ApplyPower":
                action = ApplyPowerAction(target, effect['power'], amount)
                self.action_queue.add_bottom(action)

            elif action_type == "Exhaust":
                self.action_queue.add_bottom(ExhaustAction(amount))

            elif action_type == "Discard":
                self.action_queue.add_bottom(DiscardAction(source, amount))

            elif action_type == "LoseHP":
                if target_type == "self":
                    # source 就是打出这张牌的人（玩家自身）
                    self.action_queue.add_bottom(LoseHPAction(target=source, amount=amount))

            else:
                print(f"⚠️ 引擎警告: 未知的动作类型 '{action_type}'")

        # 2. 所有动作入队完毕，启动队列流水线进行统一结算
        self.action_queue.resolve_all(self)


# ==========================================
# 1. 基础动作组件 (Action Components)
# ==========================================
class Action:
    """所有动作的基类"""

    def __init__(self):
        self.is_done = False

    def execute(self, engine):
        """所有子类必须实现此方法"""
        raise NotImplementedError("动作子类必须实现 execute(engine) 方法")


class DamageAction(Action):
    def __init__(self, source, target, amount):
        super().__init__()
        self.source = source
        self.target = target
        self.amount = amount

    def execute(self, engine):

        final_damage = calculate_final_damage(self.amount, self.source, self.target)

        if final_damage != self.amount:
            print(f"  💥 状态干预！伤害从 {self.amount} 变为 {final_damage}。")

        # 3. 护甲抵消管线 (核心修复区)
        # 安全获取目标的格挡值，如果没有该属性则默认为0
        current_block = getattr(self.target, 'block', 0)

        if current_block > 0:
            if current_block >= final_damage:
                # 护甲值充裕，完全吸收本次伤害
                self.target.block -= final_damage
                print(f"  🛡️ {self.target.name} 的格挡吸收了全部 {final_damage} 点伤害！(剩余格挡: {self.target.block})")
                final_damage = 0  # 伤害已清零，后续不再扣血
            else:
                # 护甲被击破，计算穿透的实质伤害
                final_damage -= current_block
                self.target.block = 0
                print(f"  💔 {self.target.name} 的格挡被击破！吸收了 {current_block} 点伤害。")

        # 4. 结算真实生命值伤害 (HP)
        if final_damage > 0:
            self.target.hp -= final_damage
            print(
                f"  🗡️ {self.source.name} 对 {self.target.name} 造成了 {final_damage} 点实质伤害。(剩余 HP: {self.target.hp})")

        # 5. 死亡判定中断
        if self.target.hp <= 0:
            print(f"  💀 {self.target.name} 阵亡！")
            # 如果它还在雷达里，立刻抹除！
            if self.target in engine.current_enemies:
                engine.current_enemies.remove(self.target)


class DrawCardAction(Action):
    def __init__(self, amount):
        super().__init__()
        self.amount = amount

    def execute(self, engine):
        # 如果引擎挂载了牌库管理器，则实际执行抽牌逻辑
        if engine.deck_manager:
            engine.deck_manager.draw_cards(self.amount)
        else:
            print(f"  🃏 玩家试图抽取 {self.amount} 张牌 (提示: 引擎未绑定牌库管理器)。")


# 请将这个类添加到你的 engine.py 中
class GainBlockAction(Action):
    def __init__(self, target, amount):
        super().__init__()
        self.target = target
        self.amount = amount

    def execute(self, engine):
        if not hasattr(self.target, 'block'):
            self.target.block = 0
        self.target.block += self.amount
        print(f"  🛡️ {self.target.name} 获得了 {self.amount} 点格挡。(当前格挡: {self.target.block})")


class ApplyPowerAction(Action):
    def __init__(self, target, power_id, amount):
        super().__init__()
        self.target = target
        self.power_id = power_id
        self.amount = amount

    def execute(self, engine):
        if self.power_id not in POWER_REGISTRY:
            print(f"⚠️ 引擎警告: 未注册的状态 '{self.power_id}'")
            return

        if not hasattr(self.target, 'powers'):
            self.target.powers = {}

        # 核心逻辑：如果身上已经有该状态对象，叠加层数；如果没有，实例化一个新的
        if self.power_id in self.target.powers:
            self.target.powers[self.power_id].amount += self.amount
        else:
            power_class = POWER_REGISTRY[self.power_id]
            self.target.powers[self.power_id] = power_class(self.target, self.amount)

        power_name = self.target.powers[self.power_id].name
        print(f"  ✨ {self.target.name} 被施加了 {self.amount} 层 【{power_name}】。")


# engine.py 核心重构段落

class BaseCardMoveAction(Action):
    """
    交互式卡牌流转动作基类 (通用抽象中心)
    """

    def __init__(self, amount, action_name):
        super().__init__()
        self.amount = amount
        self.action_name = action_name  # 用于 UI 渲染的词条，如 "弃牌"、"消耗"

    def get_destination_pile(self, deck_manager):
        """留给子类实现：告诉基类卡牌最终要位移到哪个具体的列表"""
        raise NotImplementedError

    def execute(self, engine):
        deck = engine.deck_manager
        dest_pile = self.get_destination_pile(deck)

        for _ in range(self.amount):
            # 1. 统一的边界防御
            if not deck.hand:
                print(f"  💨 手牌已空，无法继续进行【{self.action_name}】！")
                break

            # 2. 统一的 UI 列表渲染
            print(f"\n  📥 【动作中断】你需要选择【{self.action_name}】一张牌：")
            for i, card_name in enumerate(deck.hand):
                print(f"    [{i + 1}] {card_name}")

            # 3. 统一的阻塞式输入循环与异常捕获
            while True:
                choice = input(f"  请输入要【{self.action_name}】的卡牌编号: ")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(deck.hand):
                        # 从手牌中 pop，并压入对应的目的地堆
                        chosen_card = deck.hand.pop(idx)
                        dest_pile.append(chosen_card)
                        print(f"  ✨ 成功将 【{chosen_card}】 移入{self.action_name}堆。")
                        break
                    else:
                        print("  ❌ 无效的编号，请重新选择！")
                except ValueError:
                    print("  ❌ 请输入数字！")


# ==========================================
# 瘦身后的具体衍生动作 (Concrete Actions)
# ==========================================

class DiscardAction(BaseCardMoveAction):
    def __init__(self, source, amount):
        # 传入动词提示
        super().__init__(amount, "弃牌")
        self.source = source

    def get_destination_pile(self, deck_manager):
        # 明确目的地：弃牌堆
        return deck_manager.discard_pile


class ExhaustAction(BaseCardMoveAction):
    def __init__(self, amount):
        # 传入动词提示
        super().__init__(amount, "消耗")

    def get_destination_pile(self, deck_manager):
        # 明确目的地：消耗堆
        return deck_manager.exhaust_pile


# 在 actions.py 中新增

class LoseHPAction(Action):
    def __init__(self, target, amount):
        super().__init__()
        self.target = target
        self.amount = amount

    def execute(self, engine):
        # 扣除生命值（无视格挡）
        self.target.hp -= self.amount
        print(
            f"  🩸 【{self.target.name}】 流失了 {self.amount} 点生命值！ (HP: {max(0, self.target.hp)}/{self.target.max_hp})")

        # 死亡判定（针对玩家流血致死的情况）
        if self.target.hp <= 0:
            print(f"  💀 【{self.target.name}】 阵亡了！")
            if self.target in engine.current_enemies:
                engine.current_enemies.remove(self.target)
