#!/usr/bin/env python3
"""
Story Manifold Engine - Batch Generator (并发版)
用法: python3 batch_generate.py <worker_id> <total_workers>
例如: python3 batch_generate.py 0 5
"""

import json
import sys
import time
import urllib.request
import urllib.error
import re
import random
from pathlib import Path

DEEPSEEK_KEY = "sk-cffc51be682c4f8f859610b9528d7d48"
API_URL = "https://api.deepseek.com/v1/chat/completions"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw_skeletons"
RAW_DIR.mkdir(parents=True, exist_ok=True)

ARCHETYPES = [
    "复仇","禁忌之恋","英雄成长","权力斗争","救赎",
    "背叛与信任","失去与寻回","身份错认","流亡归来","牺牲",
    "阴谋揭露","家族对立","误会与和解","堕落与沉沦","反抗与自由",
    "寻找真相","宿命对决","双重身份","师徒传承","末路同行",
    "夺位之争","替代者","遗忘与记忆","跨越阶级的爱","复活与重生",
]

# 多样性配置池（循环使用，保证每原型20个骨架有足够变化）
ENDINGS   = ["tragedy","tragedy","pyrrhic","pyrrhic","bittersweet","bittersweet","open","open","triumph","bittersweet",
             "tragedy","pyrrhic","open","tragedy","bittersweet","pyrrhic","tragedy","open","bittersweet","pyrrhic"]
STAKES    = ["灵魂","爱情","身份","权力","生命","真相","信念","自由","荣耀","灵魂",
             "真相","身份","爱情","生命","信念","权力","灵魂","自由","真相","荣耀"]
LIT_MODES = ["literary","literary","literary","literary","mixed","literary","literary","mixed","literary","literary",
             "literary","mixed","literary","literary","literary","mixed","literary","literary","mixed","literary"]
STYLE_POOLS = [
    ["古代","家族"],["现代","悬疑"],["架空","奇幻"],["科幻","都市"],["战争","家族"],
    ["宫廷","悬疑"],["江湖","古代"],["奇幻","架空"],["现代","家族"],["都市","悬疑"],
    ["古代","宫廷"],["科幻","悬疑"],["战争","架空"],["江湖","悬疑"],["家族","现代"],
    ["奇幻","战争"],["都市","家族"],["架空","宫廷"],["古代","悬疑"],["现代","奇幻"],
]

LIT_GUIDANCE = {
    "literary": """
文学风格（严肃文学）：
- 叙事重心在内心状态与道德困境，而非外部行动
- 避免「布局」「翻盘」「绝地反击」「主动出击」等网文套语
- beats 体现模糊性、矛盾性、不可解决的张力
- 参考语感：托尔斯泰、契诃夫、余华、张爱玲、加缪
- 张力曲线可以是平缓闷烧型，不必追求戏剧性高峰""",
    "mixed": """
文学风格（严肃与类型混合）：
- 情节有动力，但人物内心同样占据叙事空间
- 避免纯粹爽感翻盘，结局留有余地和代价
- 参考：石黑一雄、格雷厄姆·格林、路遥""",
}

SYSTEM_PROMPT = """你是一个跨文化叙事结构研究者，生成"故事骨架"JSON。
actors 只使用：主角/反派/导师/盟友/爱人/家族/敌对势力
beats 共9个，tension_curve 共9个浮点数(0.0-1.0)。
输出纯 JSON，不要 markdown 包裹，不要任何额外说明。

Schema:
{"id":"sk_XXX","archetype":"原型","title":"标题(5-10字)","logline":"一句话冲突(30-60字)",
"style_tags":["标签1","标签2"],"ending":"ending值","stakes":"stakes值",
"actors":["主角",...],"beats":[{"id":1,"name":"节拍名","desc":"60-90字描述"},...],"tension_curve":[...],"themes":["主题1","主题2"]}"""

VALID_ACTORS = {"主角","反派","导师","盟友","爱人","家族","敌对势力"}

def normalize_actors(actors):
    result, seen = [], set()
    for a in actors:
        base = re.split(r"[（(【\[/／]", str(a))[0].strip()
        if base in VALID_ACTORS and base not in seen:
            seen.add(base); result.append(base)
    return result or ["主角"]

def call_api(messages, retry=3):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.92,
        "max_tokens": 1800,
    }).encode("utf-8")
    for attempt in range(retry):
        try:
            req = urllib.request.Request(API_URL, data=payload,
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  ⚠️  attempt {attempt+1}: {e}")
            if attempt < retry-1: time.sleep(3*(attempt+1))
    return None

def generate(sk_id, archetype, slot):
    """slot: 0-19，决定这是该原型的第几个骨架"""
    ending    = ENDINGS[slot]
    stakes    = STAKES[slot]
    lit_mode  = LIT_MODES[slot]
    style_tags = STYLE_POOLS[slot]
    lit_guide = LIT_GUIDANCE[lit_mode]

    user_msg = f"""为原型「{archetype}」（ID:{sk_id}）生成故事骨架。

强制约束：
- ending: {ending}
- stakes: {stakes}  
- style_tags 必须包含: {style_tags}
{lit_guide}

直接输出 JSON。"""

    raw = call_api([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])
    if not raw: return None

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip()=="```" else lines[1:]).strip()

    try:
        data = json.loads(raw)
        data["id"] = sk_id
        data["ending"] = ending
        data["stakes"] = stakes
        data["actors"] = normalize_actors(data.get("actors", []))
        # 统一 beats 字段名
        for b in data.get("beats", []):
            if "description" in b and "desc" not in b:
                b["desc"] = b.pop("description")
        return data
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON error: {e} | 前100字: {raw[:100]}")
        return None

def build_task_list():
    """构建全部475个待生成任务"""
    tasks = []
    idx = 26
    for slot in range(19):  # 第2~20轮，每轮25个原型
        for arch_idx, arch in enumerate(ARCHETYPES):
            sk_id = f"sk_{idx:03d}"
            tasks.append((sk_id, arch, slot+1))  # slot+1 因为slot0已生成
            idx += 1
    return tasks

def main():
    worker_id     = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    total_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    all_tasks = build_task_list()
    # 按 worker_id 分片
    my_tasks = [t for i, t in enumerate(all_tasks) if i % total_workers == worker_id]

    print(f"🚀 Worker {worker_id}/{total_workers} | 任务数: {len(my_tasks)}")

    ok, fail = 0, 0
    for i, (sk_id, arch, slot) in enumerate(my_tasks, 1):
        out = RAW_DIR / f"{sk_id}.json"
        if out.exists():
            print(f"[{i:3d}/{len(my_tasks)}] ⏭️  {sk_id} 已存在")
            ok += 1
            continue

        print(f"[{i:3d}/{len(my_tasks)}] 🔨 {sk_id} ({arch}) slot={slot}...", end=" ", flush=True)
        t0 = time.time()
        data = generate(sk_id, arch, slot)
        if data:
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            print(f"✅ ({time.time()-t0:.1f}s)")
            ok += 1
        else:
            print("❌")
            fail += 1

        time.sleep(random.uniform(0.8, 1.5))  # 随机抖动避免多worker同时请求

    print(f"\nWorker {worker_id} 完成: ✅{ok} ❌{fail}")

if __name__ == "__main__":
    main()
