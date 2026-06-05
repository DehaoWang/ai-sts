import random


class DeckManager:
    def __init__(self, initial_cards):
        self.master_deck = initial_cards[:]

        self.draw_pile = []
        self.hand = []
        self.discard_pile = []
        self.exhaust_pile = []

        # 战斗开始时，打乱抽牌堆
        self.shuffle_draw_pile()

    def shuffle_draw_pile(self):
        print("🔁 【系统】洗牌！")
        random.shuffle(self.draw_pile)

    def draw_cards(self, amount):
        print(f"📥 尝试抽取 {amount} 张牌...")
        drawn_cards = []  # 用于记录本次实际抽到的牌

        for _ in range(amount):
            # 规则：如果抽牌堆为空，触发弃牌堆洗入抽牌堆的逻辑
            if not self.draw_pile:
                if not self.discard_pile:
                    print("⚠️ 抽牌堆和弃牌堆均为空，无牌可抽！")
                    break
                print("🔄 抽牌堆已空，将弃牌堆洗入抽牌堆！")
                self.draw_pile = self.discard_pile[:]
                self.discard_pile = []
                self.shuffle_draw_pile()

            # 从抽牌堆顶部（列表尾部）弹出一张牌
            card = self.draw_pile.pop()
            # 3. ✋ 核心物理防线：检测手牌上限 (最大 10 张)
            if len(self.hand) >= 10:
                print(f"  🛑 手牌已满 (10/10)！【{card}】 溢出，直接进入弃牌堆。")
                self.discard_pile.append(card)
            else:
                self.hand.append(card)
                drawn_cards.append(card)

        # 循环结束后，将抽到的牌合并为一行输出
        if drawn_cards:
            print(f"🃏 抽到了: 【{', '.join(drawn_cards)}】")

    def play_card(self, card_name, cost, current_energy):
        # 模拟打出一张牌的资源检查与流转
        if card_name not in self.hand:
            print(f"❌ 你的手牌中没有 {card_name}")
            return current_energy

        if current_energy < cost:
            print(f"❌ 能量不足！需要 {cost} 费，当前仅有 {current_energy} 费。")
            return current_energy

        # 扣除费用并流转卡牌
        current_energy -= cost
        self.hand.remove(card_name)
        self.discard_pile.append(card_name)
        print(f"⚔️ 成功打出 [{card_name}]！剩余能量: {current_energy}")
        return current_energy

    def end_turn(self):
        # 规则：回合结束时，所有手牌进入弃牌堆
        print("🛑 回合结束，清理手牌...")
        self.discard_pile.extend(self.hand)
        self.hand = []

    def print_status(self):
        print(f"📊 状态统计 | 抽牌堆: {len(self.draw_pile)} | 手牌: {len(self.hand)} | 弃牌堆: {len(self.discard_pile)}")

    def reset_for_combat(self):
        """战斗开始前的牌库重置"""
        self.draw_pile =self.master_deck[:]

        self.hand.clear()
        self.discard_pile.clear()
        self.exhaust_pile.clear()
        self.shuffle_draw_pile()
