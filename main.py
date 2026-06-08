from entities import Player
from monsters import JawWorm, Cultist
from deck import DeckManager
from game import SpireClimb  # 引入我们刚刚抽离的调度器
from relics import BurningBlood, Vajra


# ==========================================
# 4. 地牢生成器 (Factory)
# ==========================================
class DungeonGenerator:
    @staticmethod
    def generate_act_1_exordium():
        """生成第一幕：塔底 (The Exordium) 的怪物分布图"""
        return [
            {"type": "combat", "generator": lambda: [JawWorm(10), JawWorm(15)]},  # 层数 1: 战斗
            {"type": "campfire"},  # 层数 2: 篝火
            {"type": "combat", "generator": lambda: [Cultist(20)]},  # 层数 3: 战斗
            {"type": "campfire"},  # 层数 2: 篝火
        ]

    @staticmethod
    def generate_act_2_city():
        """预留：生成第二幕：城市 (The City) 的怪物分布图"""
        # 可以返回完全不同的怪物列表
        return []


# ==========================================
# 5. 游戏总入口 (Director)
# ==========================================
if __name__ == "__main__":
    # --- 1. 模拟菜单交互：玩家选择角色 ---
    print("请选择你的角色:")

    # 0: 铁甲战士 (Ironclad), 1: 静默猎手 (Silent)
    pool_id = 0
    # pool_id = 1

    chosen_player = Player(name="铁甲战士", hp=80, max_energy=3, pool="Ironclad")
    chosen_player.gain_relic(BurningBlood())
    chosen_player.gain_relic(Vajra())
    starter_deck_cards = ["打击"] * 5 + ["防御"] * 4 + ["痛击", "突破"]
    chosen_deck = DeckManager(starter_deck_cards)

    if pool_id == 1:
        chosen_player = Player(name="静默猎手", hp=80, max_energy=3, pool="Silent")
        starter_deck_cards = ["打击"] * 5 + ["防御"] * 5 + ["中和", "生存者"]
        chosen_deck = DeckManager(starter_deck_cards)

    # --- 2. 模拟地图生成：生成楼层路线 ---
    # act_1_floors = DungeonGenerator.generate_act_1_exordium()

    # --- 3. 依赖注入：将玩家、牌组、楼层组装进引擎并启动 ---
    game = SpireClimb(player=chosen_player, deck=chosen_deck, total_floors=5)
    game.start()

    # todo
    # todo 1:需要Check如果没牌可烧，是否能抽牌
