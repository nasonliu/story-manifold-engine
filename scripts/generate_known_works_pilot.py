#!/usr/bin/env python3
import json, os, time, urllib.request, random
from pathlib import Path

API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.getenv("DEEPSEEK_KEY", "sk-cffc51be682c4f8f859610b9528d7d48")
MODEL = os.getenv("MODEL", "deepseek-chat")

OUT_DIR = Path("/home/nason/.openclaw/workspace/story-manifold-engine/data/raw_skeletons_known/pilot_100")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def call_api(messages, temperature=0.7, max_tokens=2500, retry=3):
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    for i in range(retry):
        try:
            req = urllib.request.Request(
                API_URL,
                data=payload,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"]
        except Exception:
            if i == retry - 1:
                raise
            time.sleep(2 + i * 2)


def get_balanced_worklist(n=100):
    sys = "你是世界文学策展人。输出纯JSON，不要markdown。"
    usr = f'''
请生成一个平衡的作品清单，目标 {n} 部“知名文学/叙事作品”（小说、戏剧、史诗、现代文学、类型文学均可），用于叙事骨架研究。
硬性要求：
1) 国别尽量均衡（至少覆盖：东亚、南亚、中东、欧洲、北美、拉美、非洲、俄语/东欧）
2) 时代均衡（古典/19世纪/20世纪/21世纪）
3) 风格均衡（现实主义/魔幻现实/科幻/侦探/爱情/成长/讽刺/存在主义/史诗等）
4) 避免同系列重复（同作者可最多2部）

输出格式：
{{"works":[{{"id":"wk_001","title":"...","author":"...","country_region":"...","era":"...","style":"...","notes":"<20字>"}}]}}
'''
    raw = call_api([{"role": "system", "content": sys}, {"role": "user", "content": usr}], temperature=0.4, max_tokens=8000)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1]).strip()
    data = json.loads(raw)
    works = data.get("works", [])[:n]
    # re-id
    for i, w in enumerate(works, 1):
        w["id"] = f"wk_{i:03d}"
    return works


def gen_skeleton(work):
    sys = '''你是叙事结构分析器。基于你已知的作品知识输出“结构骨架”，不引用原文段落，不虚构不存在角色名。
输出纯JSON，不要markdown。
Schema:
{"id":"sk_xxx","source":{"work_id":"wk_xxx","title":"","author":""},"archetype":"","title":"","logline":"","style_tags":[],"ending":"tragedy|triumph|bittersweet|open|pyrrhic","stakes":"","actors":[],"beats":[{"id":1,"name":"","desc":""}],"tension_curve":[...9 floats...],"themes":[],"confidence":0.0}
要求：
- beats严格9段；每段desc 45-90字
- tension_curve严格9个0-1浮点，整体有起伏
- confidence为你对作品记忆可靠度(0-1)
'''
    usr = f"作品: {work['title']} / {work['author']} / {work.get('country_region','')} / {work.get('era','')} / {work.get('style','')}\n请给出骨架JSON。"
    raw = call_api([{"role": "system", "content": sys}, {"role": "user", "content": usr}], temperature=0.65, max_tokens=2000)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1]).strip()
    d = json.loads(raw)
    d["source"] = {
        "work_id": work["id"],
        "title": work["title"],
        "author": work["author"],
        "country_region": work.get("country_region", ""),
        "era": work.get("era", ""),
        "style": work.get("style", ""),
    }
    d["id"] = work["id"].replace("wk_", "sk_known_")
    return d


def main():
    works_file = OUT_DIR / "works_list.json"
    if works_file.exists():
        works = json.load(open(works_file, encoding="utf-8"))
    else:
        works = get_balanced_worklist(100)
        json.dump(works, open(works_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    ok = 0
    for w in works:
        out = OUT_DIR / f"{w['id']}.json"
        if out.exists():
            ok += 1
            continue
        try:
            d = gen_skeleton(w)
            json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            ok += 1
            print(f"OK {w['id']} {w['title']}")
        except Exception as e:
            print(f"FAIL {w['id']} {w['title']} :: {e}")
        time.sleep(random.uniform(0.5, 1.2))

    print(f"DONE {ok}/{len(works)}")


if __name__ == "__main__":
    main()
