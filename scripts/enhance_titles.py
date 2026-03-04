#!/usr/bin/env python3
"""
Title Enhancement Module - Fix title duplication
Generate alternative titles for high-frequency titles
"""
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

DATA_DIR = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/cleaned_skeletons')
REPORT_DIR = Path('/home/nason/.openclaw/workspace/story-manifold-engine/reports')

# Title enhancement patterns
TITLE_PREFIXES = [
    "暗影", "迷雾", "灰烬", "星火", "余烬", "残阳", "寒霜", "春风",
    "暮色", "黎明", "黄昏", "夜雨", "孤灯", "断剑", "血痕", "梦魇",
    "往事前", "尘封", "破碎", "重生", "陨落", "觉醒", "沉沦", "救赎",
]

TITLE_SUFFIXES = [
    "之谜", "之殇", "之路", "之歌", "之舞", "之火", "之冰", "之血",
    "的代价", "的救赎", "的终局", "的起源", "的秘密", "的真相",
    "往事", "追忆", "挽歌", "独白", "变奏", "残响",
]

TITLE_MODIFIERS = [
    "新编", "外传", "前传", "续章", "变奏", "重构",
]

def load_skeletons() -> List[dict]:
    with open(DATA_DIR / 'skeletons_v2.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def find_duplicate_titles(skeletons: List[dict], threshold: int = 10) -> Dict[str, List[dict]]:
    """Find titles that appear more than threshold times."""
    title_map = {}
    for sk in skeletons:
        title = sk.get('title', '').strip()
        if title:
            if title not in title_map:
                title_map[title] = []
            title_map[title].append(sk)
    
    return {t: items for t, items in title_map.items() if len(items) > threshold}

def generate_title_variants(original_title: str, archetype: str = "", seed: int = 0) -> List[str]:
    """Generate title variants using patterns + random."""
    import random
    random.seed(hash(original_title) + seed)
    
    variants = []
    
    # Try prefix insertion
    if random.random() > 0.5:
        prefix = random.choice(TITLE_PREFIXES)
        variants.append(f"{prefix}{original_title}")
    
    # Try suffix addition
    if random.random() > 0.5:
        suffix = random.choice(TITLE_SUFFIXES)
        variants.append(f"{original_title}{suffix}")
    
    # Try modifier prefix
    if random.random() > 0.7:
        modifier = random.choice(TITLE_MODIFIERS)
        variants.append(f"{modifier}{original_title}")
    
    # Try archetype-based variation
    if archetype:
        if random.random() > 0.5:
            variants.append(f"{archetype}{random.choice(['', '：'])}{original_title}")
    
    return variants

def enhance_titles(skeletons: List[dict], max_duplicates: int = 5) -> Tuple[List[dict], Dict]:
    """Enhance titles to reduce duplication."""
    # First pass: count titles
    title_counter = Counter(sk.get('title', '') for sk in skeletons if sk.get('title'))
    
    # Track changes
    changes = {}
    processed = set()
    
    for sk in skeletons:
        title = sk.get('title', '').strip()
        if title in processed:
            continue
            
        count = title_counter.get(title, 0)
        if count <= max_duplicates:
            processed.add(title)
            continue
        
        # Need to modify some duplicates
        archetype = sk.get('archetype', '')
        variants = generate_title_variants(title, archetype)
        
        # Assign variants to duplicates
        dup_indices = [i for i, s in enumerate(skeletons) if s.get('title') == title]
        
        for idx in dup_indices[max_duplicates:]:
            if variants:
                new_title = variants.pop(0) if variants else f"{title}·{idx}"
                old_title = skeletons[idx].get('title', '')
                skeletons[idx]['title'] = new_title
                changes[old_title] = changes.get(old_title, []) + [new_title]
                processed.add(new_title)
    
    return skeletons, changes

def run_enhancement():
    """Run title enhancement."""
    print("Loading skeletons...")
    skeletons = load_skeletons()
    print(f"Loaded {len(skeletons)} skeletons")
    
    # Find duplicates
    print("Finding duplicate titles...")
    duplicates = find_duplicate_titles(skeletons, threshold=5)
    print(f"Found {len(duplicates)} titles with >5 duplicates")
    
    for title, items in sorted(duplicates.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {title}: {len(items)}")
    
    # Enhance
    print("\nEnhancing titles...")
    enhanced, changes = enhance_titles(skeletons, max_duplicates=3)
    
    # Save
    output_path = DATA_DIR / 'skeletons_v2_enhanced.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")
    
    # Report
    print(f"\nTotal changes: {len(changes)}")
    for orig, new_titles in list(changes.items())[:5]:
        print(f"  {orig} -> {new_titles}")
    
    return enhanced, changes

if __name__ == "__main__":
    run_enhancement()
