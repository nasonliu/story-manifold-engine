#!/usr/bin/env python3
import json, os, time, random, re, urllib.request
from pathlib import Path

API_URL = "https://api.deepseek.com/v1/chat/completions"
LIST_MODEL = os.getenv("LIST_MODEL", "deepseek-chat")
GEN_MODEL = os.getenv("GEN_MODEL", "deepseek-chat")

OUT_DIR = Path("/home/nason/.openclaw/workspace/story-manifold-engine/data/raw_skeletons_known/batch_1k")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    ("史诗与历史", 120),
    ("现实主义", 120),
    ("爱情", 100),
    ("成长", 80),
    ("侦探与悬疑", 100),
    ("科幻", 100),
    ("奇幻", 100),
    ("讽刺与黑色幽默", 70),
    ("存在主义与心理", 70),
    ("实验叙事", 60),
    ("幽默", 50),
    ("通俗类型", 30),
]
assert sum(x[1] for x in CATEGORIES) == 1000


def call_api(model, messages, temperature=0.7, max_tokens=2500, retry=4):
    api_key = os.getenv("DEEPSEEK_KEY", "")
    if not api_key:
        raise RuntimeError("DEEPSEEK_KEY missing")
    req_obj = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if "reasoner" not in model:
        req_obj["response_format"] = {"type": "json_object"}
    payload = json.dumps(req_obj).encode("utf-8")
    for i in range(retry):
        try:
            req = urllib.request.Request(
                API_URL,
                data=payload,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
        except Exception:
            if i == retry - 1:
                raise
            time.sleep(2 + i * 2)


def _strip_code_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if len(lines) >= 3:
            raw = "\n".join(lines[1:-1]).strip()
    return raw


def _extract_json_object(raw: str) -> str:
    # greedy fallback: take first {...} block
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise json.JSONDecodeError("No JSON object found", raw, 0)
    return m.group(0)


def parse_json(raw: str):
    raw = _strip_code_fence(raw)
    try:
        return json.loads(raw)
    except Exception:
        obj = _extract_json_object(raw)
        return json.loads(obj)


def make_category_list(cat: str, n: int):
    sys = "你是文学策展助手。输出纯JSON，不要markdown。"
    usr = f'''
请为题材“{cat}”生成 {n} 部知名叙事作品名单，用于骨架抽取。
要求：
1) 尽量覆盖不同地区与时代（但不需要硬配额）
2) 避免同一作者超过2部，避免同系列重复
3) 必须是叙事作品（小说/戏剧/史诗/中短篇/类型文学）
4) 不要输出解释

输出：{{"works":[{{"title":"...","author":"...","country_region":"...","era":"...","style":"..."}}]}}
'''
    last_err = None
    for t in range(4):
        try:
            raw = call_api(LIST_MODEL, [{"role": "system", "content": sys}, {"role": "user", "content": usr}], temperature=0.3, max_tokens=7000)
            data = parse_json(raw)
            works = data.get("works", [])
            if isinstance(works, list) and works:
                return works[:n]
            raise RuntimeError("empty works list")
        except Exception as e:
            last_err = e
            time.sleep(1.5 + t)
    raise last_err


def build_1k_list():
    all_works = []
    seen = set()
    for cat, quota in CATEGORIES:
        remain = quota
        chunk_size = 25
        cat_works = []
        fail_streak = 0
        no_progress_streak = 0
        rounds = 0
        max_rounds = max(20, quota * 2)
        print(f"[LIST] start category={cat} quota={quota}", flush=True)
        while remain > 0:
            rounds += 1
            if rounds > max_rounds:
                print(f"[LIST][WARN] category={cat} hit max_rounds={max_rounds}, keep={len(cat_works)}/{quota}", flush=True)
                break
            n = min(chunk_size, remain)
            before = len(cat_works)
            try:
                got = make_category_list(cat, n + 10)
                fail_streak = 0
            except Exception as e:
                fail_streak += 1
                print(f"[LIST][WARN] category={cat} chunk={n} fail_streak={fail_streak} err={e}", flush=True)
                if chunk_size > 10:
                    chunk_size = max(10, chunk_size - 5)
                if fail_streak >= 8:
                    print(f"[LIST][ERROR] category={cat} too many failures, continue retry loop", flush=True)
                    fail_streak = 0
                time.sleep(random.uniform(1.0, 2.0))
                continue

            for w in got:
                key = (w.get("title", "").strip(), w.get("author", "").strip())
                if not key[0] or key in seen:
                    continue
                seen.add(key)
                w["category"] = cat
                cat_works.append(w)
                if len(cat_works) >= quota:
                    break

            gained = len(cat_works) - before
            if gained == 0:
                no_progress_streak += 1
            else:
                no_progress_streak = 0

            if no_progress_streak >= 6:
                print(f"[LIST][WARN] category={cat} no progress for {no_progress_streak} rounds, break with {len(cat_works)}/{quota}", flush=True)
                break

            remain = quota - len(cat_works)
            print(f"[LIST] category={cat} progress={len(cat_works)}/{quota} total={len(all_works)+len(cat_works)}", flush=True)
            time.sleep(random.uniform(0.8, 1.5))
        all_works.extend(cat_works[:quota])

    for i, w in enumerate(all_works, 1):
        w["id"] = f"wk_{i:04d}"
    return all_works[:1000]


def gen_skeleton(work):
    sys = '''你是叙事结构分析器。基于你已知作品知识输出结构骨架，不引用原文段落。
输出纯JSON。
Schema:
{"id":"sk_xxx","source":{"work_id":"wk_xxx","title":"","author":"","category":""},"archetype":"","title":"","logline":"","style_tags":[],"ending":"tragedy|triumph|bittersweet|open|pyrrhic","stakes":"","actors":[],"beats":[{"id":1,"name":"","desc":""}],"tension_curve":[...9 floats...],"themes":[],"confidence":0.0}
要求：beats严格9段；tension_curve严格9个0-1浮点。'''
    usr = f"作品：{work['title']} / {work['author']} / 题材:{work.get('category','')} / 风格:{work.get('style','')}"

    last_err = None
    for t in range(4):
        try:
            raw = call_api(GEN_MODEL, [{"role": "system", "content": sys}, {"role": "user", "content": usr}], temperature=0.65, max_tokens=2200)
            d = parse_json(raw)
            beats = d.get("beats", [])
            tension = d.get("tension_curve", [])
            if not isinstance(beats, list) or len(beats) != 9:
                raise RuntimeError(f"invalid beats len: {len(beats) if isinstance(beats, list) else 'NA'}")
            if not isinstance(tension, list) or len(tension) != 9:
                raise RuntimeError(f"invalid tension len: {len(tension) if isinstance(tension, list) else 'NA'}")
            d["id"] = work["id"].replace("wk_", "sk_known_")
            d["source"] = {
                "work_id": work["id"],
                "title": work.get("title", ""),
                "author": work.get("author", ""),
                "country_region": work.get("country_region", ""),
                "era": work.get("era", ""),
                "style": work.get("style", ""),
                "category": work.get("category", ""),
            }
            return d
        except Exception as e:
            last_err = e
            time.sleep(1.0 + t)
    raise last_err


def main():
    works_file = OUT_DIR / "works_list_1k.json"
    if works_file.exists():
        works = json.load(open(works_file, encoding="utf-8"))
    else:
        works = build_1k_list()
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
            print(f"FAIL {w['id']} {w.get('title','')} :: {e}")
        time.sleep(random.uniform(0.4, 1.0))

    print(f"DONE {ok}/{len(works)}")


if __name__ == "__main__":
    main()
