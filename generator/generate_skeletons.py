#!/usr/bin/env python3
"""
Story Manifold Engine - Skeleton Generator v2
纯标准库实现，无需 openai 包，直接调 DeepSeek API
v2: 强化严肃文学权重，支持 ending/stakes/style 多样性强制分配
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
DEEPSEEK_KEY = "sk-cffc51be682c4f8f859610b9528d7d48"
API_URL = "https://api.deepseek.com/v1/chat/completions"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw_skeletons"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 25 个原型（第二批 026-050 用，或重新生成 001-025）──
ARCHETYPES = [
    ("sk_001", "复仇"),
    ("sk_002", "禁忌之恋"),
    ("sk_003", "英雄成长"),
    ("sk_004", "权力斗争"),
    ("sk_005", "救赎"),
    ("sk_006", "背叛与信任"),
    ("sk_007", "失去与寻回"),
    ("sk_008", "身份错认"),
    ("sk_009", "流亡归来"),
    ("sk_010", "牺牲"),
    ("sk_011", "阴谋揭露"),
    ("sk_012", "家族对立"),
    ("sk_013", "误会与和解"),
    ("sk_014", "堕落与沉沦"),
    ("sk_015", "反抗与自由"),
    ("sk_016", "寻找真相"),
    ("sk_017", "宿命对决"),
    ("sk_018", "双重身份"),
    ("sk_019", "师徒传承"),
    ("sk_020", "末路同行"),
    ("sk_021", "夺位之争"),
    ("sk_022", "替代者"),
    ("sk_023", "遗忘与记忆"),
    ("sk_024", "跨越阶级的爱"),
    ("sk_025", "复活与重生"),
]

# ── 强制多样性分配表（每个原型指定 ending + stakes + 文学倾向）──
# lit_weight: "literary"=严肃文学优先, "genre"=类型文学, "mixed"=混合
CONSTRAINTS = {
    "sk_001": {"ending": "pyrrhic",     "stakes": "灵魂",   "lit_weight": "literary"},
    "sk_002": {"ending": "tragedy",     "stakes": "爱情",   "lit_weight": "literary"},
    "sk_003": {"ending": "open",        "stakes": "身份",   "lit_weight": "mixed"},
    "sk_004": {"ending": "tragedy",     "stakes": "权力",   "lit_weight": "literary"},
    "sk_005": {"ending": "bittersweet", "stakes": "灵魂",   "lit_weight": "literary"},
    "sk_006": {"ending": "open",        "stakes": "信念",   "lit_weight": "literary"},
    "sk_007": {"ending": "bittersweet", "stakes": "身份",   "lit_weight": "literary"},
    "sk_008": {"ending": "tragedy",     "stakes": "身份",   "lit_weight": "literary"},
    "sk_009": {"ending": "pyrrhic",     "stakes": "荣耀",   "lit_weight": "mixed"},
    "sk_010": {"ending": "tragedy",     "stakes": "生命",   "lit_weight": "literary"},
    "sk_011": {"ending": "pyrrhic",     "stakes": "真相",   "lit_weight": "literary"},
    "sk_012": {"ending": "tragedy",     "stakes": "信念",   "lit_weight": "literary"},
    "sk_013": {"ending": "open",        "stakes": "爱情",   "lit_weight": "mixed"},
    "sk_014": {"ending": "tragedy",     "stakes": "灵魂",   "lit_weight": "literary"},
    "sk_015": {"ending": "pyrrhic",     "stakes": "自由",   "lit_weight": "literary"},
    "sk_016": {"ending": "bittersweet", "stakes": "真相",   "lit_weight": "literary"},
    "sk_017": {"ending": "pyrrhic",     "stakes": "荣耀",   "lit_weight": "mixed"},
    "sk_018": {"ending": "tragedy",     "stakes": "身份",   "lit_weight": "literary"},
    "sk_019": {"ending": "bittersweet", "stakes": "信念",   "lit_weight": "literary"},
    "sk_020": {"ending": "tragedy",     "stakes": "生命",   "lit_weight": "literary"},
    "sk_021": {"ending": "pyrrhic",     "stakes": "权力",   "lit_weight": "literary"},
    "sk_022": {"ending": "open",        "stakes": "身份",   "lit_weight": "literary"},
    "sk_023": {"ending": "bittersweet", "stakes": "真相",   "lit_weight": "literary"},
    "sk_024": {"ending": "tragedy",     "stakes": "爱情",   "lit_weight": "literary"},
    "sk_025": {"ending": "open",        "stakes": "灵魂",   "lit_weight": "literary"},
}

# ── 文学风格补充说明（根据 lit_weight 注入 prompt）──
LIT_GUIDANCE = {
    "literary": """
文学风格要求（严肃文学优先）：
- 叙事重心在内心状态与道德困境，而非外部行动序列
- 避免「布局」「翻盘」「绝地反击」「主动出击」等网文套语
- beats 描述应体现模糊性、矛盾性、不可解决的张力，而非清晰的因果推进
- 结局不需要正义被伸张、问题被解决——可以是崩塌、沉默、徒劳
- 参考语感：托尔斯泰、契诃夫、陀思妥耶夫斯基、加缪、张爱玲、余华
- 张力曲线可以是平缓的闷烧型（如 [0.3,0.4,0.5,0.6,0.7,0.6,0.5,0.4,0.2]），不必追求戏剧性高峰
""",
    "mixed": """
文学风格要求（严肃与类型混合）：
- 情节有动力，但人物内心世界同样占据叙事空间
- 避免纯粹的爽感翻盘，结局留有余地和代价
- 参考：格雷厄姆·格林、石黑一雄、路遥
- 张力曲线有明显起伏，但高潮后应有真实的代价感（末尾不高扬）
""",
    "genre": """
文学风格要求（类型文学基础上提升质感）：
- 情节驱动，但人物动机需有心理深度，非单纯工具性
- 结局可以是 triumph，但胜利应有代价
""",
}

SYSTEM_PROMPT = """你是一个跨文化叙事结构研究者。你的任务是为给定的故事原型生成一个"故事骨架"（Story Skeleton）。

骨架是纯结构性的，不依赖具体设定——它描述的是叙事节拍序列、张力曲线、核心冲突机制。
不要写具体角色名、地名，用角色类型代替：主角 / 反派 / 导师 / 盟友 / 爱人 / 家族 / 敌对势力。

严格按照以下 JSON schema 输出，不要输出任何其他内容，不要用 markdown 代码块包裹：

{
  "id": "sk_XXX",
  "archetype": "原型名称",
  "title": "骨架标题（5-10字，抽象、文学性）",
  "logline": "一句话概括核心冲突（30-60字，可以有模糊性和张力，不需要是清晰的动作句）",
  "style_tags": ["标签1", "标签2"],
  "ending": "tragedy 或 triumph 或 bittersweet 或 open 或 pyrrhic",
  "stakes": "生命 或 权力 或 爱情 或 真相 或 身份 或 自由 或 荣耀 或 信念 或 灵魂",
  "actors": ["主角", ...],
  "beats": [
    {"id": 1, "name": "节拍名（3-6字，文学性）", "desc": "60-90字，重心在内心状态、道德张力、人物关系的微妙变化，而非外部事件序列"},
    ...
  ],
  "tension_curve": [0.1, 0.4, ...],
  "themes": ["主题1", "主题2"]
}

通用要求：
- beats 共 9 个，tension_curve 也必须是 9 个浮点数（0.0-1.0）
- style_tags 从以下选 2-3 个：古代/现代/架空/科幻/奇幻/悬疑/战争/家族/江湖/宫廷/都市/校园
- actors 只使用标准类型：主角/反派/导师/盟友/爱人/家族/敌对势力，可选其中几个
- 输出纯 JSON，不要 markdown 包裹"""


def call_api(messages: list, retry: int = 3) -> str | None:
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.9,
        "max_tokens": 1800,
    }).encode("utf-8")

    for attempt in range(retry):
        try:
            req = urllib.request.Request(
                API_URL,
                data=payload,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"\n  ⚠️  HTTP {e.code} (attempt {attempt+1}): {body[:200]}")
        except Exception as e:
            print(f"\n  ⚠️  错误 (attempt {attempt+1}): {e}")
        if attempt < retry - 1:
            time.sleep(3 * (attempt + 1))
    return None


def generate_skeleton(skeleton_id: str, archetype: str) -> dict | None:
    c = CONSTRAINTS.get(skeleton_id, {})
    ending = c.get("ending", "bittersweet")
    stakes = c.get("stakes", "信念")
    lit_weight = c.get("lit_weight", "mixed")
    lit_guide = LIT_GUIDANCE[lit_weight]

    user_msg = f"""请为原型「{archetype}」（ID: {skeleton_id}）生成故事骨架。

强制约束（必须严格遵守）：
- ending 必须是：{ending}
- stakes 必须是：{stakes}

{lit_guide}

直接输出 JSON，不要任何额外说明。"""

    raw = call_api([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])

    if not raw:
        return None

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    raw = raw.strip()

    try:
        data = json.loads(raw)
        data["id"] = skeleton_id
        # 强制覆盖 ending/stakes，防止模型忽略约束
        data["ending"] = ending
        data["stakes"] = stakes
        # 标准化 actors
        data["actors"] = normalize_actors(data.get("actors", []))
        return data
    except json.JSONDecodeError as e:
        print(f"\n  ❌ JSON解析失败: {e}")
        print(f"  原始内容前300字: {raw[:300]}")
        return None


VALID_ACTORS = {"主角", "反派", "导师", "盟友", "爱人", "家族", "敌对势力"}

def normalize_actors(actors: list) -> list:
    import re
    result = []
    seen = set()
    for a in actors:
        base = re.split(r"[（(【\[]", str(a))[0].strip()
        base = re.split(r"[/／]", base)[0].strip()
        canonical = base if base in VALID_ACTORS else None
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result if result else ["主角"]


def main(force_regenerate: bool = False):
    print("🚀 Story Skeleton Generator v2 (文学增强版)")
    print(f"📂 输出: {OUTPUT_DIR}")
    print(f"📊 共 {len(ARCHETYPES)} 个原型\n")

    results = []
    failed = []

    for i, (sk_id, archetype) in enumerate(ARCHETYPES, 1):
        out_file = OUTPUT_DIR / f"{sk_id}.json"
        c = CONSTRAINTS.get(sk_id, {})

        if out_file.exists() and not force_regenerate:
            try:
                with open(out_file, encoding="utf-8") as f:
                    existing = json.load(f)
                print(f"[{i:2d}/25] ⏭️  {sk_id} ({archetype}) — 已存在，跳过")
                results.append(existing)
                continue
            except Exception:
                pass

        ending_hint = c.get('ending', '?')
        stakes_hint = c.get('stakes', '?')
        lit_hint = c.get('lit_weight', '?')
        print(f"[{i:2d}/25] 🔨 {sk_id} ({archetype}) [{ending_hint}/{stakes_hint}/{lit_hint}]...", end=" ", flush=True)
        t0 = time.time()
        skeleton = generate_skeleton(sk_id, archetype)
        elapsed = time.time() - t0

        if skeleton:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(skeleton, f, ensure_ascii=False, indent=2)
            results.append(skeleton)
            print(f"✅ ({elapsed:.1f}s)")
        else:
            failed.append((sk_id, archetype))
            print(f"❌ 失败")

        time.sleep(1)

    # 写合并文件
    merged_dir = OUTPUT_DIR.parent / "cleaned_skeletons"
    merged_dir.mkdir(exist_ok=True)
    merged_path = merged_dir / "skeletons.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ 成功: {len(results)} 个  ❌ 失败: {len(failed)} 个")
    if failed:
        print(f"失败列表: {[f'{a}({b})' for a, b in failed]}")
    print(f"📄 合并文件: {merged_path}")

    # 分布统计
    from collections import Counter
    endings = Counter(sk['ending'] for sk in results)
    stakes  = Counter(sk['stakes']  for sk in results)
    print("\n=== Ending 分布 ===")
    for k, v in endings.most_common(): print(f"  {k}: {'█'*v} {v}")
    print("=== Stakes 分布 ===")
    for k, v in stakes.most_common():  print(f"  {k}: {'█'*v} {v}")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    main(force_regenerate=force)
