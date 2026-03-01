#!/usr/bin/env python3
"""
actors 字段标准化
将带括号描述的细化角色名归并为 7 个标准类型：
  主角 / 反派 / 导师 / 盟友 / 爱人 / 家族 / 敌对势力
其余特殊角色也尽量映射进来；无法映射的保留原样并打印警告。
"""

import json
import re
from pathlib import Path

INPUT  = Path(__file__).parent.parent / "data" / "cleaned_skeletons" / "skeletons.json"
OUTPUT = INPUT  # 原地覆盖

# ── 映射规则（前缀优先匹配）────────────────────────────────
CANONICAL = [
    "主角", "反派", "导师", "盟友", "爱人", "家族", "敌对势力"
]

# 额外别名 → 标准类型
ALIAS_MAP = {
    # 主角变体
    "主角": "主角",
    # 反派变体
    "反派": "反派",
    "宿敌": "反派",
    "幕后黑手": "反派",
    "背叛者": "反派",
    "抹除者": "反派",
    "操控势力": "反派",
    "统治者": "反派",
    "腐败势力": "反派",
    # 导师变体
    "导师": "导师",
    "师父": "导师",
    "神秘导师": "导师",
    "记忆守护者": "导师",
    # 盟友变体
    "盟友": "盟友",
    "新盟友": "盟友",
    "盟友团体": "盟友",
    "失忆盟友": "盟友",
    "误导者": "盟友",        # 伪盟友也归盟友（语义上是盟友角色的变体）
    "追索者": "盟友",
    "需要被保护的无辜者": "盟友",
    "失踪者": "盟友",
    "受害者": "盟友",
    "绝望的幸存者群体": "盟友",
    # 爱人变体
    "爱人": "爱人",
    # 家族变体
    "家族": "家族",
    "甲族族长": "家族",
    "乙族族长": "家族",
    "家族长老": "家族",
    "家族象征": "家族",
    "家族盟友": "家族",
    "家族势力": "家族",
    # 敌对势力变体
    "敌对势力": "敌对势力",
    "反派势力": "敌对势力",
    "敌对势力首领": "敌对势力",
    "权威势力": "敌对势力",
    "冷酷的追猎势力": "敌对势力",
    "系统化身": "敌对势力",
}


def normalize_one(raw: str) -> str:
    """将单个 actor 字符串归并为标准类型。"""
    raw = raw.strip()
    # 1. 去掉括号内容，取前缀
    base = re.split(r"[（(]", raw)[0].strip()
    # 2. 精确匹配别名表
    if base in ALIAS_MAP:
        return ALIAS_MAP[base]
    # 3. 前缀匹配（处理"导师/启蒙者"这种带斜杠的）
    base_slash = re.split(r"[/／]", base)[0].strip()
    if base_slash in ALIAS_MAP:
        return ALIAS_MAP[base_slash]
    # 4. 实在匹配不上，保留原样并警告
    print(f"  ⚠️  未映射: {repr(raw)} → 保留原值")
    return raw


def normalize_actors(actors: list[str]) -> list[str]:
    normalized = [normalize_one(a) for a in actors]
    # 去重，保持顺序
    seen = set()
    result = []
    for a in normalized:
        if a not in seen:
            seen.add(a)
            result.append(a)
    return result


def main():
    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    print(f"📂 处理 {len(data)} 个骨架...\n")

    for sk in data:
        old = sk.get("actors", [])
        new = normalize_actors(old)
        if old != new:
            print(f"  {sk['id']} {sk['archetype']}")
            print(f"    原: {old}")
            print(f"    新: {new}")
        sk["actors"] = new

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 标准化完成，已写回 {OUTPUT}")

    # 统计结果
    from collections import Counter
    all_actors = [a for sk in data for a in sk["actors"]]
    print("\n=== 标准化后 actors 分布 ===")
    for k, v in Counter(all_actors).most_common():
        bar = "█" * v
        print(f"  {k:8s} {bar} {v}")


if __name__ == "__main__":
    main()
