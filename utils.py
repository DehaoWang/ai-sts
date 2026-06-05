# utils.py

def calculate_final_damage(base_damage, source, target):
    """
    通用伤害结算管线 (核心数学模型)
    """
    dmg = base_damage

    # 1. 攻击方乘区 (如：力量计算、虚弱)，力量优先级最高，确保它在最前面被处理
    if source and hasattr(source, 'powers'):
        sorted_source_powers = sorted(source.powers.values(), key=lambda p: p.priority)
        for power in sorted_source_powers:
            dmg = power.at_damage_give(dmg)

    # 2. 防御方乘区 (如：易伤计算)
    if target and hasattr(target, 'powers'):
        sorted_target_powers = sorted(target.powers.values(), key=lambda p: p.priority)
        for power in sorted_target_powers:
            dmg = power.at_damage_receive(dmg)

    return max(0, int(dmg))
