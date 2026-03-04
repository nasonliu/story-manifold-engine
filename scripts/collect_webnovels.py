#!/usr/bin/env python3
"""
Web Novel Collector
Collect Chinese web novels from various sources
"""
import json
import requests
from pathlib import Path
from typing import List, Dict

OUTPUT_FILE = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/to_process_webnovels.json')

# Popular Chinese web novel genres
GENRES = [
    "玄幻", "都市", "历史", "仙侠", "游戏", "科幻", 
    "奇幻", "武侠", "悬疑", "轻小说"
]

# Known popular novels (manual seed data)
KNOWN_NOVELS = [
    {"title": "盘龙", "author": "我吃西红柿", "genre": "玄幻"},
    {"title": "完美世界", "author": "辰东", "genre": "玄幻"},
    {"title": "遮天", "author": "辰东", "genre": "仙侠"},
    {"title": "凡人修仙传", "author": "忘语", "genre": "仙侠"},
    {"title": "斗破苍穹", "author": "天蚕土豆", "genre": "玄幻"},
    {"title": "星辰变", "author": "我吃西红柿", "genre": "玄幻"},
    {"title": "雪中悍刀行", "author": "烽火戏诸侯", "genre": "武侠"},
    {"title": "庆余年", "author": "猫腻", "genre": "历史"},
    {"title": "间客", "author": "猫腻", "genre": "科幻"},
    {"title": "将夜", "author": "猫腻", "genre": "玄幻"},
    {"title": "择天记", "author": "猫腻", "genre": "仙侠"},
    {"title": "全职高手", "author": "蝴蝶蓝", "genre": "游戏"},
    {"title": "全职法师", "author": "乱", "genre": "玄幻"},
    {"title": "万族之劫", "author": "老鹰吃小鸡", "genre": "玄幻"},
    {"title": "稳住别浪", "author": "跳舞", "genre": "都市"},
    {"title": "深空彼岸", "author": "辰东", "genre": "科幻"},
    {"title": "夜的命名术", "author": "会说话的肘子", "genre": "都市"},
    {"title": "灵境行者", "author": "卖报小郎君", "genre": "都市"},
    {"title": "不科学御兽", "author": "轻泉流响", "genre": "玄幻"},
    {"title": "轮回乐园", "author": "那一只蚊子", "genre": "玄幻"},
]

def generate_sample_plot(title: str, genre: str) -> str:
    """Generate a placeholder plot for known novels."""
    return f"《{title}》是一部{genre}类小说，讲述主角在异世界修炼成长，历经磨难最终成为强者的故事。"

def collect_known_novels() -> List[Dict]:
    """Collect known popular novels."""
    novels = []
    for novel in KNOWN_NOVELS:
        novels.append({
            "title": novel["title"],
            "author": novel["author"],
            "genre": novel["genre"],
            "plot": generate_sample_plot(novel["title"], novel["genre"]),
            "source": "known_classics"
        })
    return novels

def main():
    print("Collecting web novels...")
    
    # Collect known novels
    novels = collect_known_novels()
    print(f"Collected {len(novels)} known novels")
    
    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f"Existing: {len(existing)} novels")
    
    # Merge (avoid duplicates)
    existing_titles = set(e.get('title', '') for e in existing)
    new_novels = [n for n in novels if n['title'] not in existing_titles]
    
    all_novels = existing + new_novels
    
    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_novels, f, ensure_ascii=False, indent=2)
    
    print(f"Total: {len(all_novels)} novels")

if __name__ == "__main__":
    main()
