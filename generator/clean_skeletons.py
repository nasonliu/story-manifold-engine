#!/usr/bin/env python3
"""
Story Skeleton 清洗 & 去重脚本
用法：python clean_skeletons.py
"""
import json
import re
import sys
from pathlib import Path

RAW_DIR = Path("data/raw_skeletons")
OUT_FILE = Path("data/cleaned_skeletons/skeletons.json")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

VALID_ENDINGS = {"tragedy", "triumph", "bittersweet", "open", "pyrrhic"}

def validate(sk: dict) -> bool:
    try:
        assert isinstance(sk.get("id"), str)
        assert isinstance(sk.get("archetype"), list) and len(sk["archetype"]) >= 1
        beats = sk.get("beats", [])
        assert 6 <= len(beats) <= 14, f"beats={len(beats)}"
        for b in beats:
            assert isinstance(b.get("event"), str) and len(b["event"]) > 3
        assert sk.get("ending") in VALID_ENDINGS, f"ending={sk.get('ending')}"
        assert isinstance(sk.get("twist_count"), int)
        return True
    except AssertionError as e:
        print(f"  Invalid [{sk.get('id','?')}]: {e}")
        return False

def deduplicate(skeletons: list) -> list:
    """Simple dedup by id and beat-signature"""
    seen_ids = set()
    seen_sigs = set()
    result = []
    for sk in skeletons:
        sid = sk.get("id", "")
        sig = "|".join(b["event"][:10] for b in sk.get("beats", []))
        if sid in seen_ids or sig in seen_sigs:
            print(f"  Duplicate: {sid}")
            continue
        seen_ids.add(sid)
        seen_sigs.add(sig)
        result.append(sk)
    return result

def main():
    all_skeletons = []
    for f in sorted(RAW_DIR.glob("*.json")):
        print(f"Loading {f.name}...")
        with open(f) as fp:
            data = json.load(fp)
        if isinstance(data, list):
            all_skeletons.extend(data)
        else:
            all_skeletons.append(data)

    print(f"\nTotal loaded: {len(all_skeletons)}")

    valid = [sk for sk in all_skeletons if validate(sk)]
    print(f"Valid: {len(valid)}")

    deduped = deduplicate(valid)
    print(f"After dedup: {len(deduped)}")

    # Re-assign sequential IDs
    for i, sk in enumerate(deduped, 1):
        sk["id"] = f"sk_{i:04d}"

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved {len(deduped)} skeletons → {OUT_FILE}")

if __name__ == "__main__":
    main()
