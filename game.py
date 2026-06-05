# game.py
from engine import GameEngine
from cards import CARD_DB, CARD_POOLS
import random


# ==========================================
# 1. 爬塔管理器 (Macro-Run)
# ==========================================
class SpireClimb:
    def __init__(self, player, deck, floors):
        self.player = player
        self.deck = deck
        self.engine = GameEngine(deck_manager=self.deck)
        self.floors = floors

    def start(self):
        print("\n" + "*" * 50)
        print("🌋 欢迎来到杀戮尖塔！你的试炼即将开始...")
        print("*" * 50)

        for current_floor, node in enumerate(self.floors, start=1):
            node_type = node.get("type")
            if node_type == "combat":
                enemy = node["generator"]()
                survived = run_combat(self.player, self.deck, self.engine, enemy, current_floor)

                if not survived:
                    print("\n" + "💀 " * 15)
                    print(f"你倒在了第 {current_floor} 层。高塔依然矗立。")
                    print("💀 " * 15)
                    return

                # todo 战斗胜利后奖励：恢复生命值、获得卡牌、获得遗物等
                heal_amount = 6
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                print(
                    f"\n🎉 战斗胜利！搜刮战利品：恢复 {heal_amount} 点生命值。(当前 HP: {self.player.hp}/{self.player.max_hp})")

                # 👇 触发战利品系统，传入当前楼层以计算升级掉落率
                run_card_reward(self.player, self.deck, current_floor)

            elif node_type == "campfire":
                # 触发篝火逻辑
                run_campfire(self.player, self.deck)

            input("\n>>> 按回车键前往下一层 <<<")

        print("\n" + "👑 " * 15)
        print("传说中的心脏就在眼前... 恭喜通关测试版尖塔！")
        print("👑 " * 15)


# ==========================================
# 2. 单场战斗引擎 (Micro-Combat)
# ==========================================
def run_combat(player, deck, engine, enemy, floor_num):
    """
    负责执行一场完整的战斗。
    返回 True 表示玩家胜利，False 表示玩家死亡。
    """
    print("\n" + "=" * 50)
    print(f"🏰 【第 {floor_num} 层】 遭遇战开始！ 敌人: 【{enemy.name}】")
    print("=" * 50)

    # 战前重置：洗牌、清空上一局的状态和格挡
    deck.reset_for_combat()
    player.powers.clear()
    player.clear_block()

    turn_count = 1
    # enemy.roll_intent()
    # enemy.apply_powers(player)

    draw_num = 5  # 每回合抽牌数

    # --- 核心状态机循环 ---
    while player.hp > 0 and enemy.hp > 0:
        print(f"\n【第 {turn_count} 回合开始】")
        enemy.roll_intent()
        enemy.apply_powers(player)

        # ==================================
        # 1. 玩家回合阶段
        # ==================================
        player.energy = player.max_energy
        player.clear_block()  # 玩家回合开始，清空玩家上一回合的格挡
        deck.draw_cards(draw_num)

        # 玩家操作阶段
        while True:
            status_str_player = ", ".join([str(p) for p in player.powers.values()]) if player.powers else "无"
            status_str_enemy = ", ".join([str(p) for p in enemy.powers.values()]) if enemy.powers else "无"

            print("-" * 40)
            print(
                f"👤 {player.name} | HP: {player.hp}/{player.max_hp} | 格挡: {player.block} "
                f"| 状态: [{status_str_player}] | 能量: {player.energy}/{player.max_energy}")
            print(
                f"👾 {enemy.name} | HP: {enemy.hp}/{enemy.max_hp} | 格挡: {enemy.block} "
                f"| 状态: [{status_str_enemy}]")
            print("-" * 40)

            hand_options = [f"[{i + 1}] {name}({CARD_DB[name]['cost']}费)" for i, name in enumerate(deck.hand)]

            # 👇 1. UI 提示增加 [v] 查看牌堆
            print(f"【你的手牌】: {' | '.join(hand_options)} | [0] 结束回合 | [v] 查看牌堆")
            print("-" * 50)

            choice = input("打出卡牌编号 (0 结束回合, v 查看牌堆): ").strip().lower()
            if choice == '0':
                break

            # 👇 2. 核心拦截：如果是 v，则呼出透视面板，并使用 continue 重新刷新输入循环
            if choice == 'v':
                print("\n" + "=" * 15 + " 🔍 牌堆透视镜 (DEBUG) " + "=" * 15)
                print(f"🗂️ 抽牌堆 ({len(deck.draw_pile)}张): {', '.join(deck.draw_pile) if deck.draw_pile else '空'}")
                print(f"🖐️ 手牌库 ({len(deck.hand)}张): {', '.join(deck.hand) if deck.hand else '空'}")
                print(
                    f"🗑️ 弃牌堆 ({len(deck.discard_pile)}张): {', '.join(deck.discard_pile) if deck.discard_pile else '空'}")
                print(
                    f"🔥 消耗堆 ({len(deck.exhaust_pile)}张): {', '.join(deck.exhaust_pile) if deck.exhaust_pile else '空'}")
                print("=" * 55 + "\n")
                continue  # 跳过本轮后续判断，直接重新回到等待玩家出牌的状态

            try:
                card_index = int(choice) - 1
                if 0 <= card_index < len(deck.hand):
                    card_name = deck.hand[card_index]
                    card_data = CARD_DB[card_name]

                    if player.energy >= card_data['cost']:
                        player.energy -= card_data['cost']
                        deck.hand.pop(card_index)

                        # 👇 【核心升级】：读取 JSON 中的 is_exhaust 属性
                        if card_data.get("is_exhaust", False):
                            deck.exhaust_pile.append(card_name)
                            print(f"  🔥 【{card_name}】 能量耗尽，已被消耗！")
                        else:
                            deck.discard_pile.append(card_name)

                        engine.play_card(card_data, source=player, target=enemy)
                        if enemy.hp <= 0:
                            break
                    else:
                        print("❌ 能量不足！")
                else:
                    print("❌ 无效的编号！")
            except ValueError:
                print("❌ 请输入数字！")

            enemy.apply_powers(player)  # 实时更新敌人意图数值（如：被削弱后伤害降低）

        if enemy.hp <= 0:
            break

        # 玩家回合结束结算
        deck.end_turn()

        # ==================================
        # 2. 怪物回合阶段
        # ==================================
        print("\n" + "-" * 20)
        # 【时序修复 2】：怪物回合开始，清空它上一回合残留的格挡
        enemy.clear_block()

        # 怪物执行上回合宣告的意图 (可能会获得新格挡)
        enemy.execute_intent(engine, player)
        engine.action_queue.resolve_all(engine)

        # 【时序修复 3】：双方执行完意图后，结算它的状态效果（如：流血伤害、持续增益等）
        enemy.tick_powers()
        player.tick_powers()

        print("-" * 20)

        turn_count += 1

    return player.hp > 0


# 篝火事件
def run_campfire(player, deck):
    print("\n" + "=" * 50)
    print("🔥 【休息处】 你来到了一处篝火。火焰劈啪作响，让你感到温暖。")
    print("=" * 50)

    while True:
        print(f"当前状态 | HP: {player.hp}/{player.max_hp}")
        print("[1] 💤 休息 (恢复 30% 最大生命值)")
        print("[2] 🔨 锻造 (永久升级牌组中的一张牌)")

        choice = input("请选择你的行动: ").strip()

        if choice == '1':
            heal_amount = int(player.max_hp * 0.3)
            player.hp = min(player.max_hp, player.hp + heal_amount)
            print(f"\n  💤 你在温暖的篝火旁睡了个好觉。恢复了 {heal_amount} 点生命值。")
            break

        elif choice == '2':
            # 过滤出牌库中尚未升级的牌 (不包含 '+' 结尾的)
            upgradeable_cards = [card for card in deck.master_deck if not card.endswith('+')]

            if not upgradeable_cards:
                print("\n  ❌ 你的牌组中已经没有可以升级的牌了！请重新选择。")
                continue

            print("\n  锤打声响起，请选择要强化的卡牌：")
            for i, card in enumerate(upgradeable_cards):
                print(f"    [{i + 1}] {card}")
            print("    [0] 返回上级菜单")

            smith_choice = input("  请输入卡牌编号: ").strip()
            if smith_choice == '0':
                continue

            try:
                idx = int(smith_choice) - 1
                if 0 <= idx < len(upgradeable_cards):
                    card_to_upgrade = upgradeable_cards[idx]

                    # 核心机制：在基础牌组中找到这张牌，并替换为带 '+' 的版本
                    # 因为我们在 deck.py 里的 master_deck 是个字符串列表
                    master_idx = deck.master_deck.index(card_to_upgrade)
                    deck.master_deck[master_idx] = card_to_upgrade + "+"

                    print(f"\n  🔨 叮！火花四溅！你的 【{card_to_upgrade}】 永久升级为了 【{card_to_upgrade}+】！")
                    break
                else:
                    print("  ❌ 无效的编号。")
            except ValueError:
                print("  ❌ 请输入数字。")
        else:
            print("❌ 无效的选择，请输入 1 或 2。")


# ==========================================
# 卡牌掉落奖励 (Card Reward Screen)
# ==========================================
def run_card_reward(player, deck, current_floor):
    print("\n" + "=" * 50)
    print("🎁 【战利品结算】 战斗胜利！发现了一些卡牌，你可以选择一张加入牌组！")
    print("=" * 50)

    # 1. 获取玩家对应阵营的掉落池
    pool_name = player.pool
    available_cards = CARD_POOLS.get(pool_name, [])
    print("非基础量")
    print(len(available_cards))

    if len(available_cards) < 3:
        print("  ⚠️ 卡池深度不足，无法生成完整的三选一奖励。")
        return

    # 2. 从基础卡池中随机抽出 3 张不同的牌
    base_options = random.sample(available_cards, 3)
    reward_options = []

    # 🌟 动态升级概率计算：基础 10%，每往上一层增加 1%
    upgrade_chance = 0.10 + (current_floor * 0.01)

    # 3. 核心机制：变异判定
    for card_name in base_options:
        if random.random() < upgrade_chance:
            upgraded_name = card_name + "+"
            # 去全局数据库查户口，确保这张牌真的配置了升级版
            if upgraded_name in CARD_DB:
                reward_options.append(upgraded_name)
            else:
                reward_options.append(card_name)
        else:
            reward_options.append(card_name)

    # 4. UI 渲染与玩家交互
    while True:
        print("\n  请选择你要拿取的卡牌：")
        for i, card_name in enumerate(reward_options):
            card_data = CARD_DB[card_name]
            cost = card_data.get('cost', 0)

            # 动态抓取效果生成简易描述
            desc_fragments = []
            for effect in card_data.get('effects', []):
                action = effect.get('action')
                amount = effect.get('amount', '')
                desc_fragments.append(f"{action}:{amount}")
            desc_preview = " | ".join(desc_fragments) if desc_fragments else "无特殊效果"

            # 视觉高亮升级牌
            highlight = "✨ (已升级)" if card_name.endswith('+') else ""
            print(f"    [{i + 1}] 【{card_name}】 ({cost}费) {highlight}- 效果: {desc_preview}")

        print("    [0] 🚫 放弃选择 (跳过)")

        choice = input("\n  请输入编号: ").strip()

        if choice == '0':
            print("  💨 你看了一眼，觉得这些牌会污染你的牌库，果断选择跳过。")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < 3:
                chosen_card = reward_options[idx]

                # 🌟 核心：直接塞入玩家的“永久牌库”
                deck.master_deck.append(chosen_card)

                print(f"\n  🎉 你获得了 【{chosen_card}】！它已加入你的永久牌库。")
                break
            else:
                print("  ❌ 无效的编号，请重新选择。")
        except ValueError:
            print("  ❌ 请输入数字。")