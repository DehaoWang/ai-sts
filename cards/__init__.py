import os
import json
import copy  # 👈 必须引入 copy 模块用于深拷贝

CARD_DB = {}
CARD_POOLS = {}

current_dir = os.path.dirname(os.path.abspath(__file__))

# 【核心升级】：使用 os.walk 递归遍历当前目录及所有子目录
for root, dirs, files in os.walk(current_dir):
    for filename in files:
        if filename.endswith(".json"):
            file_path = os.path.join(root, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    card_data = json.load(f)
                    base_name = card_data["name"]

                    # 1. 装入全局数据库 (基础版)
                    CARD_DB[base_name] = card_data

                    # 2. 读取阵营并分类 (⚠️ 只有基础牌进入掉落池)
                    pool_name = card_data.get("pool", "Neutral")
                    rarity = card_data.get("rarity", "Common")  # 未填写的默认为普通牌
                    if rarity != "Basic":  # 基础牌不进入掉落池
                        if pool_name not in CARD_POOLS:
                            CARD_POOLS[pool_name] = []
                        CARD_POOLS[pool_name].append(base_name)

                    # 3. 自动检测并衍生升级版卡牌 (+)
                    if "upgrade" in card_data:
                        # 确保内存指针完全隔离
                        upgraded_card = copy.deepcopy(card_data)
                        upgraded_card["name"] = base_name + "+"

                        # 用增量数据覆盖本体
                        for key, override_value in card_data["upgrade"].items():
                            upgraded_card[key] = override_value

                        # 清理无用的 upgrade 节点，保持最终数据的纯净
                        del upgraded_card["upgrade"]

                        # 升级版仅存入全局数据库，供打牌引擎和篝火强化使用
                        # (不执行 CARD_POOLS.append，防止野生升级牌泛滥)
                        CARD_DB[upgraded_card["name"]] = upgraded_card

            except json.JSONDecodeError:
                print(f"⚠️ [系统] 卡牌文件格式损坏，已跳过: {filename}")
            except Exception as e:
                print(f"⚠️ [系统] 加载卡牌时发生未知错误 {filename}: {e}")

print(f"📦 成功加载 {len(CARD_DB)} 张卡牌 (包含衍生升级形态)。")
print(f"🗂️ 基础掉落卡池分布: { {k: len(v) for k, v in CARD_POOLS.items()} }")
print(f"🔍 卡牌数据库预览: {list(CARD_DB.keys())[:50]}...")