#!/usr/bin/env python3
"""
Narrative Physics Generator v1
生成具有真实结构多样性的故事骨架

状态向量 s（结构参数）→ 约束求解 → beat 序列

参数空间：
- L: beats 数量 (3-15)
- C: climax 位置 (0.4-0.9)
- R: reversals 数量 (0-3)
- Tshape: 张力曲线类型 (ramp, hill, double_peak, wave, drop_then_rise)
- I: 信息不对称程度 (0-2)
- Delay: 伏笔回收延迟 (0-2)
- K: 冲突源数量 (1-3)
- Cross: 冲突耦合度 (0-2)
- Agency: 主角能动性 (0-2)
- Closure: 结局闭合度 (0-2)
"""
import json, random, math
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter


# ============ 张力曲线函数 ============
def get_tension_curve(L: int, tshape: str) -> List[float]:
    """生成张力曲线 t[0..L-1]，值域 0.0-1.0"""
    t = []
    for i in range(L):
        x = i / max(L - 1, 1)  # 0 到 1
        
        if tshape == "ramp":
            # 递增
            val = x
        elif tshape == "hill":
            # 单峰
            val = math.sin(x * math.pi)
        elif tshape == "double_peak":
            # 双峰
            if x < 0.5:
                val = math.sin(x * 2 * math.pi)
            else:
                val = math.sin(x * 2 * math.pi) * 0.7
        elif tshape == "wave":
            # 波浪
            val = (math.sin(x * 4 * math.pi) + 1) / 2
        elif tshape == "drop_then_rise":
            # 先降后升 (V shape + rise)
            if x < 0.4:
                val = 0.8 - x * 1.5
            else:
                val = 0.2 + (x - 0.4) * 1.3
        else:
            val = 0.5
        
        t.append(max(0.0, min(1.0, val)))
    
    return t


def get_climax_beat(L: int, C: float) -> int:
    """计算 climax 发生的 beat 索引"""
    climax_beat = round(C * (L - 1))
    return max(0, min(L - 1, climax_beat))


# ============ Beat 角色定义 ============
BEAT_ROLES = ["setup", "progress", "pressure", "reversal", "reveal", "climax", "resolution"]


def get_beat_role(i: int, L: int, climax_beat: int, R: int) -> str:
    """根据位置确定 beat 角色"""
    if i == climax_beat:
        return "climax"
    elif i == 0:
        return "setup"
    elif i == L - 1:
        return "resolution"
    elif i < climax_beat * 0.3:
        return "setup"
    elif i < climax_beat * 0.7:
        return "progress"
    elif i < climax_beat:
        return "pressure"
    elif i > climax_beat and i < L - 2:
        return "reversal" if i % max(1, (L - climax_beat) // max(R, 1)) == 0 else "reveal"
    else:
        return "resolution"


# ============ 冲突系统 ============
CONFLICT_TYPES = ["external", "institutional", "internal", "environmental", "fate"]


def generate_conflicts(K: int, Cross: int) -> List[Dict]:
    """生成 K 个冲突源"""
    conflicts = []
    used = random.sample(CONFLICT_TYPES, min(K, len(CONFLICT_TYPES)))
    
    for i, ctype in enumerate(used):
        conflict = {
            "id": f"c{i}",
            "type": ctype,
            "state": "active"
        }
        conflicts.append(conflict)
    
    return conflicts


# ============ 信息不对称系统 ============
def generate_info_asymmetry(I: int, Delay: int, L: int) -> List[Dict]:
    """生成伏笔-setup-payoff 结构"""
    info_events = []
    
    num_secrets = max(1, I + Delay)  # 至少 1 个
    
    for i in range(num_secrets):
        # setup: 埋伏笔
        setup_beat = random.randint(0, max(0, L - 4))
        
        # payoff: 回收（根据 Delay 决定距离）
        min_payoff = setup_beat + 1 + Delay
        max_payoff = setup_beat + 3 + Delay * 2
        # 确保范围有效
        if min_payoff > L - 1:
            min_payoff = L - 1
        if max_payoff > L - 1:
            max_payoff = L - 1
        if min_payoff > max_payoff:
            payoff_beat = min_payoff
        else:
            payoff_beat = random.randint(min_payoff, max_payoff)
        
        info_events.append({
            "setup_beat": setup_beat,
            "payoff_beat": payoff_beat,
            "type": "misunderstanding" if I >= 1 else "hidden_info"
        })
    
    return info_events


# ============ 主生成函数 ============
def generate_skeleton(
    L: int = None,
    C: float = None,
    R: int = None,
    Tshape: str = None,
    I: int = None,
    Delay: int = None,
    K: int = None,
    Cross: int = None,
    Agency: int = None,
    Closure: int = None,
    archetype: str = None,
    seed: int = None
) -> Dict[str, Any]:
    """生成单个故事骨架"""
    
    if seed is not None:
        random.seed(seed)
    
    # 随机采样参数
    L = L or random.randint(3, 15)
    C = C or random.uniform(0.4, 0.9)
    R = R or random.randint(0, 3)
    Tshape = Tshape or random.choice(["ramp", "hill", "double_peak", "wave", "drop_then_rise"])
    I = I if I is not None else random.randint(0, 2)
    Delay = Delay if Delay is not None else random.randint(0, 2)
    K = K or random.randint(1, 3)
    Cross = Cross if Cross is not None else random.randint(0, 2)
    Agency = Agency if Agency is not None else random.randint(0, 2)
    Closure = Closure if Closure is not None else random.randint(0, 2)
    
    # 计算张力曲线
    tension_curve = get_tension_curve(L, Tshape)
    climax_beat = get_climax_beat(L, C)
    
    # 生成 beats
    beats = []
    conflicts = generate_conflicts(K, Cross)
    info_events = generate_info_asymmetry(I, Delay, L)
    
    for i in range(L):
        role = get_beat_role(i, L, climax_beat, R)
        tension = tension_curve[i]
        
        # 信息变化
        info_delta = 0
        for ev in info_events:
            if i == ev["setup_beat"]:
                info_delta = -1  # 隐藏信息
            elif i == ev["payoff_beat"]:
                info_delta = 1   # 揭示信息
        
        # 状态变化
        state_delta = "same"
        if role == "reversal":
            state_delta = random.choice(["goal_shift", "stake_increase", "advantage_flip"])
        
        # 能动性
        advantage = "none"
        if i > 0 and i < L // 2:
            advantage = "protagonist" if Agency >= 1 else "antagonist"
        elif i >= L // 2:
            advantage = "protagonist" if Agency >= 2 else "antagonist"
        
        beat = {
            "index": i,
            "role": role,
            "tension": round(tension, 2),
            "info_delta": info_delta,
            "state_delta": state_delta,
            "advantage": advantage,
            "stakes": random.choice([-1, 0, 1]) if role in ["pressure", "reversal", "climax"] else 0
        }
        beats.append(beat)
    
    # 结局
    ending_map = {0: "open", 1: "semi_open", 2: "closed"}
    ending = ending_map.get(Closure, "open")
    
    # 构建骨架
    skeleton = {
        "id": f"sk_{random.randint(100000, 999999)}",
        "archetype": archetype or f"archetype_{random.randint(1, 50)}",
        "beats": beats,
        "turning_points": [{"beat": i, "type": beats[i]["state_delta"]} 
                          for i in range(L) if beats[i]["role"] == "reversal"],
        "climax_position": C,
        "ending": ending,
        "structure_params": {
            "L": L,
            "C": round(C, 2),
            "R": R,
            "Tshape": Tshape,
            "I": I,
            "Delay": Delay,
            "K": K,
            "Cross": Cross,
            "Agency": Agency,
            "Closure": Closure
        }
    }
    
    return skeleton


def generate_dataset(n: int, seed: int = 42) -> List[Dict]:
    """生成分层均匀的数据集"""
    random.seed(seed)
    
    skeletons = []
    
    # 分层采样：确保覆盖所有维度
    # Beats: 3-15 分 5 桶
    L_buckets = [
        (3, 5), (6, 8), (9, 10), (11, 12), (13, 15)
    ]
    # Climax: 0.4-0.9 分 5 桶
    C_buckets = [
        (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9)
    ]
    # Reversals: 0-3
    R_values = [0, 1, 2, 3]
    # Tshape: 5 种
    Tshapes = ["ramp", "hill", "double_peak", "wave", "drop_then_rise"]
    
    # 每种组合生成足够样本
    per_combo = max(1, n // (len(L_buckets) * len(C_buckets) * len(R_values) * len(Tshapes)))
    
    count = 0
    for L_low, L_high in L_buckets:
        for C_low, C_high in C_buckets:
            for R in R_values:
                for Tshape in Tshapes:
                    for _ in range(per_combo):
                        if count >= n:
                            break
                        
                        L = random.randint(L_low, L_high)
                        C = random.uniform(C_low, C_high)
                        
                        skeleton = generate_skeleton(
                            L=L, C=C, R=R, Tshape=Tshape,
                            I=random.randint(0, 2),
                            Delay=random.randint(0, 2),
                            K=random.randint(1, 3),
                            Cross=random.randint(0, 2),
                            Agency=random.randint(0, 2),
                            Closure=random.randint(0, 2)
                        )
                        skeletons.append(skeleton)
                        count += 1
                    
                    if count >= n:
                        break
                if count >= n:
                    break
            if count >= n:
                break
        if count >= n:
            break
    
    return skeletons[:n]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500, help="生成数量")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/narrative_physics/skeletons_v1.json")
    args = parser.parse_args()
    
    print(f"Generating {args.n} skeletons with Narrative Physics...")
    skeletons = generate_dataset(args.n, args.seed)
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(skeletons, ensure_ascii=False, indent=2))
    print(f"Saved: {args.output}")
    print(f"Generated: {len(skeletons)}")
    
    # 验证多样性
    L_vals = [s["structure_params"]["L"] for s in skeletons]
    C_vals = [s["structure_params"]["C"] for s in skeletons]
    R_vals = [s["structure_params"]["R"] for s in skeletons]
    T_vals = [s["structure_params"]["Tshape"] for s in skeletons]
    
    print("\n=== 结构多样性验证 ===")
    print(f"L (beats): {min(L_vals)}-{max(L_vals)}, mean={sum(L_vals)/len(L_vals):.1f}")
    print(f"C (climax): {min(C_vals):.2f}-{max(C_vals):.2f}, mean={sum(C_vals)/len(C_vals):.2f}")
    print(f"R (reversals): {Counter(R_vals)}")
    print(f"Tshape: {Counter(T_vals)}")
