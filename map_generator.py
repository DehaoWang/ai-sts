import random

from entities import Entity
from monsters import JawWorm, Cultist

# ==========================================
# 怪物遭遇池 (Encounter Pools)
# ==========================================

# 1. 普通怪物池 (包含单体和多体组合)
NORMAL_ENCOUNTERS = [
    # {
    #     "name": "大颚虫",
    #     "generator": lambda: [JawWorm("大颚虫", hp=40)]
    # },
    {
        "name": "邪教徒",
        "generator": lambda: [Cultist("邪教徒", hp=40)]
    },
    # {
    #     "name": "邪教徒双人组",
    #     "generator": lambda: [Cultist("邪教徒A", hp=45), Cultist("邪教徒B", hp=45)]
    # },
]

# 2. 关底 Boss 池
BOSS_ENCOUNTERS = [
    {
        "name": "六火亡魂",
        "generator": lambda: [Entity("六火亡魂", hp=250)]
    },
    {
        "name": "守护者",
        "generator": lambda: [Entity("守护者", hp=240)]
    }
]


class SpireMapGenerator:
    def __init__(self, total_floors=16):
        self.total_floors = max(4, total_floors)

    def generate_map(self):
        # ... (之前的逻辑完全不变) ...
        # 只需要在调用 _create_combat_node 时，不再传固定名字，而是只传 is_boss 标识
        floors = []
        boss_floor = self.total_floors
        campfire_floor = self.total_floors - 1
        treasure_floor = (self.total_floors // 2) + 1

        for floor_num in range(1, self.total_floors + 1):
            if floor_num == treasure_floor:
                floors.append({"type": "treasure", "name": "古老宝箱"})
            elif floor_num == campfire_floor:
                floors.append({"type": "campfire", "name": "战前营地"})
            elif floor_num == boss_floor:
                # 👇 告诉生成器：这里要抽 Boss！
                floors.append(self._create_combat_node(is_boss=True))
            else:
                # 👇 告诉生成器：这里抽普通怪！
                floors.append(self._create_combat_node(is_boss=False))

        return floors

    # 🌟 核心改造：从数据池中抽取，取代硬编码
    def _create_combat_node(self, is_boss=False):
        """
        从对应的怪物池中随机抽取一个遭遇战组合，并返回节点配置。
        """
        if is_boss:
            # 从 Boss 池随机抽一个字典
            encounter = random.choice(BOSS_ENCOUNTERS)
        else:
            # 从普通怪物池随机抽一个字典
            encounter = random.choice(NORMAL_ENCOUNTERS)

        return {
            "type": "combat",
            "name": encounter["name"],
            "is_boss": is_boss,
            "generator": encounter["generator"]  # 必须传递这个 lambda 函数，等待主循环去调用！
        }
