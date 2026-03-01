#!/usr/bin/env python3
"""
合并所有 raw_skeletons/*.json → cleaned_skeletons/skeletons.json
并输出统计报告
"""
import json
from pathlib import Path
from collections import Counter

RAW_DIR    = Path(__file__).parent.parent / "data" / "raw_skeletons"
MERGED_OUT = Path(__file__).parent.parent / "data" / "cleaned_skeletons" / "skeletons.json"
MERGED_OUT.parent.mkdir(parents=True, exist_ok=True)

files = sorted(RAW_DIR.glob("sk_*.json"))
data = []
errors = []
for f in files:
    try:
        d = json.loads(f.read_text())
        # 保证 beats desc 字段统一
        for b in d.get("beats", []):
            if "description" in b and "desc" not in b:
                b["desc"] = b.pop("description")
        data.append(d)
    except Exception as e:
        errors.append((f.name, str(e)))

MERGED_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))

print(f"✅ 合并完成: {len(data)} 个骨架")
if errors:
    print(f"❌ 解析失败: {errors}")

# 统计
archetypes = Counter(d.get("archetype") for d in data)
endings    = Counter(d.get("ending")    for d in data)
stakes     = Counter(d.get("stakes")    for d in data)

print(f"\n=== 每原型数量 ===")
for arch, cnt in sorted(archetypes.items(), key=lambda x:-x[1]):
    bar = "█" * cnt
    print(f"  {arch:10s} {bar} {cnt}")

print(f"\n=== Ending 分布 ===")
for k,v in endings.most_common(): print(f"  {k:12s} {'█'*v} {v}")

print(f"\n=== Stakes 分布 ===")
for k,v in stakes.most_common():  print(f"  {k:6s} {'█'*v} {v}")
