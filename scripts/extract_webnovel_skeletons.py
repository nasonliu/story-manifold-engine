#!/usr/bin/env python3
"""
Extract skeleton from novel using rule-based method
Fallback when no LLM API available
"""
import json
import re
from pathlib import Path

def extract_skeleton_from_plot(plot: str, title: str, genre: str = "玄幻") -> dict:
    """
    Extract skeleton using rule-based method.
    """
    # Simple heuristic-based extraction
    sentences = re.split(r'[。！？\n]', plot)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Estimate total parts
    total_parts = max(1, len(sentences) // 10)
    
    # Generate beats based on story length
    beat_count = min(9, max(6, total_parts))
    
    # Generate tension curve (simple pattern)
    tension_curve = []
    for i in range(beat_count):
        pos = i / (beat_count - 1) if beat_count > 1 else 0.5
        # Classic story arc: low -> rising -> climax -> falling -> resolution
        if pos < 0.2:
            t = 0.2 + pos * 2  # 0.2 -> 0.6
        elif pos < 0.7:
            t = 0.6 + (pos - 0.2) * 0.8  # 0.6 -> 1.0
        else:
            t = 1.0 - (pos - 0.7) * 2  # 1.0 -> 0.4
        tension_curve.append(round(t, 2))
    
    # Generate beat names based on genre/tension
    beat_templates = {
        "玄幻": ["初始", "觉醒", "修炼", "挑战", "危机", "突破", "决战", "成道", "结局"],
        "都市": ["入职", "困境", "机遇", "成长", "危机", "反击", "成功", "稳定", "未来"],
        "仙侠": ["凡尘", "入门", "修炼", "历险", "危机", "顿悟", "斗法", "飞升", "仙界"],
        "科幻": ["背景", "发现", "研究", "危机", "应对", "突破", "决战", "新生", "延续"],
        "游戏": ["新手", "成长", "副本", "竞技", "危机", "觉醒", "巅峰", "退役", "传承"],
    }
    
    beat_names = beat_templates.get(genre, beat_templates["玄幻"])
    
    beats = []
    for i in range(beat_count):
        beats.append({
            "id": i + 1,
            "name": beat_names[i] if i < len(beat_names) else f"阶段{i+1}",
            "desc": sentences[i*3] if i*3 < len(sentences) else f"这是{title}的第{i+1}个情节点。"
        })
    
    # Determine archetype and ending based on genre patterns
    archetype = "成长"
    if "复仇" in plot[:100]:
        archetype = "复仇"
    elif "爱情" in plot[:100] or "爱" in plot[:100]:
        archetype = "爱情"
    elif "救" in plot[:100]:
        archetype = "救赎"
    
    # Simple ending inference
    endings = ["tragedy", "triumph", "bittersweet", "open", "pyrrhic"]
    ending = endings[hash(title) % len(endings)]
    
    return {
        "id": f"extracted_{hash(title) % 100000:05d}",
        "title": title,
        "archetype": archetype,
        "logline": plot[:100] + "..." if len(plot) > 100 else plot,
        "style_tags": [genre],
        "ending": ending,
        "stakes": "命运",
        "actors": ["主角", "配角"],
        "beats": beats,
        "tension_curve": tension_curve,
        "themes": [genre, archetype],
        "quality_score": 60.0
    }

def main():
    # Load web novels
    input_file = Path("data/to_process_webnovels.json")
    output_file = Path("data/real_novels/webnovels_skeletons.json")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        novels = json.load(f)
    
    print(f"Processing {len(novels)} web novels...")
    
    skeletons = []
    for i, novel in enumerate(novels):
        title = novel.get('title', f'Novel_{i}')
        plot = novel.get('plot', '')[:2000]  # Limit length
        genre = novel.get('genre', '玄幻')
        
        skeleton = extract_skeleton_from_plot(plot, title, genre)
        skeleton['source'] = 'webnovel'
        skeleton['original_genre'] = genre
        skeletons.append(skeleton)
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i+1}/{len(novels)}")
    
    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(skeletons, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(skeletons)} skeletons to {output_file}")
    
    # Stats
    archetypes = {}
    endings = {}
    for s in skeletons:
        a = s.get('archetype', 'unknown')
        e = s.get('ending', 'unknown')
        archetypes[a] = archetypes.get(a, 0) + 1
        endings[e] = endings.get(e, 0) + 1
    
    print(f"\nArchetype distribution: {archetypes}")
    print(f"Ending distribution: {endings}")

if __name__ == "__main__":
    main()
