#!/usr/bin/env python3
"""
Extract skeleton from web novel plot using LLM
"""
import json
import os
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm

DATA_FILE = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/to_process_webnovels.json')
OUTPUT_FILE = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/real_novels/webnovels_skeletons.json')

# Ensure output dir exists
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

EXTRACT_PROMPT = """你是一个故事结构分析专家。根据下面的网文情节，提取关键的结构信息。

## 输出格式 (JSON)
{
    "title": "小说标题",
    "genre": "类型标签",
    "source": "来源",
    "total_parts": 总章节数(如不知道写1),
    "beats": [
        {"id": 1, "name": "节点名称", "desc": "节点描述(50-100字)"},
        ...
    ],
    "tension_curve": [0.2, 0.3, 0.5, 0.7, 0.8, 0.6, 0.4, 0.3, 0.2],
    "themes": ["主题1", "主题2"],
    "ending_type": "tragedy/triumph/bittersweet/open/pyrrhic",
    "archetype": "原型(如复仇/成长/救赎等)"
}

## 要求
1. beats 数量: 6-10 个
2. 每个 beat 必须有 name 和 desc
3. tension_curve 长度与 beats 数量一致
4. 从情节中推断 genre, archetype, ending_type
5. 只提取信息，不要编造

## 情节内容
{plot}
"""

def extract_skeleton(item: dict, max_retries: int = 3) -> dict:
    """Extract skeleton from plot."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "你是一个专业的故事结构分析专家。"},
                    {"role": "user", "content": EXTRACT_PROMPT.format(plot=item.get('plot', '')[:8000])}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=2000,
            )
            
            result = json.loads(response.choices[0].message.content)
            result['source'] = item.get('source', 'webnovel')
            result['original_title'] = item.get('title', '')
            return result
            
        except Exception as e:
            print(f"[attempt {attempt+1}] Error: {e}")
    
    return {"error": "failed", "original": item.get('title', '')}

def main():
    # Load data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        webnovels = json.load(f)
    
    print(f"Total web novels: {len(webnovels)}")
    
    # Extract skeletons
    skeletons = []
    for item in tqdm(webnovels, desc="Extracting"):
        skeleton = extract_skeleton(item)
        skeletons.append(skeleton)
    
    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(skeletons, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(skeletons)} skeletons to {OUTPUT_FILE}")
    
    # Stats
    success = len([s for s in skeletons if 'error' not in s])
    print(f"Success: {success}/{len(skeletons)}")

if __name__ == "__main__":
    main()
