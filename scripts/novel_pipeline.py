#!/usr/bin/env python3
"""
Real Novel Skeleton Extraction Pipeline
Using local DeepSeek 8B via Ollama
"""
import json
import requests
import re
import time
from pathlib import Path
from typing import List, Dict, Optional

# Config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:8b"

DATA_DIR = Path("/home/nason/.openclaw/workspace/story-manifold-engine/data")
RAW_DIR = DATA_DIR / "real_novels_raw"
SKELETON_DIR = DATA_DIR / "real_novels_skeletons"

RAW_DIR.mkdir(parents=True, exist_ok=True)
SKELETON_DIR.mkdir(parents=True, exist_ok=True)

def make_prompt(text: str) -> str:
    """Create extraction prompt."""
    text = text[:4000]
    return f'''从下面的小说文本中提取结构信息。

输出格式（严格按此格式）:
TITLE: 故事标题
AUTHOR: 作者名
LANGUAGE: 语言(zh/en/ja/ko/fr/de/ru/es)
GENRE: 类型(玄幻/都市/仙侠/历史/游戏/科幻/悬疑/爱情/冒险/犯罪)
SUMMARY: 50字以内故事概要
CHAPTER_COUNT: 估计章节数
BEATS: 1. 激励事件描述 2. 第一个转折点描述 3. 中点描述 4. 危机描述 5. 高潮描述 6. 解决描述
TURNING_POINTS: 0.1, 0.3, 0.5, 0.7, 0.9
CLIMAX_POSITION: 0.7
TENSION_CURVE: 0.1,0.2,0.3,0.5,0.7,0.9,1.0,0.7,0.5,0.3

小说文本:
{text}

请直接输出上述格式，不要其他内容:'''

def extract_skeleton(text: str, title: str = "Unknown", max_retries: int = 2) -> Optional[Dict]:
    """Extract skeleton using local Ollama model."""
    
    prompt = make_prompt(text)
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_ctx": 8192}
                },
                timeout=120
            )
            
            if response.status_code == 200:
                content = response.json().get('response', '')
                skeleton = parse_response(content, title)
                if skeleton:
                    return skeleton
                    
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
    
    return None

def parse_response(content: str, title: str) -> Optional[Dict]:
    """Parse model response into skeleton."""
    
    skeleton = {
        "title": title,
        "author": "",
        "language": "zh",
        "genre": "",
        "structure": {
            "beats": [],
            "turning_points": [],
            "climax_position": 0.7,
            "tension_curve": []
        },
        "summary": "",
        "chapter_count": 0
    }
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("TITLE:"):
            skeleton["title"] = line.replace("TITLE:", "").strip() or title
        elif line.startswith("AUTHOR:"):
            skeleton["author"] = line.replace("AUTHOR:", "").strip()
        elif line.startswith("LANGUAGE:"):
            skeleton["language"] = line.replace("LANGUAGE:", "").strip()[:2]
        elif line.startswith("GENRE:"):
            skeleton["genre"] = line.replace("GENRE:", "").strip()
        elif line.startswith("SUMMARY:"):
            skeleton["summary"] = line.replace("SUMMARY:", "").strip()
        elif line.startswith("CHAPTER_COUNT:"):
            try:
                skeleton["chapter_count"] = int(line.replace("CHAPTER_COUNT:", "").strip())
            except:
                pass
        elif line.startswith("TURNING_POINTS:"):
            pts = line.replace("TURNING_POINTS:", "").strip()
            skeleton["structure"]["turning_points"] = [float(x) for x in pts.replace(",", " ").split() if x.replace(".","").isdigit()]
        elif line.startswith("CLIMAX_POSITION:"):
            try:
                skeleton["structure"]["climax_position"] = float(line.replace("CLIMAX_POSITION:", "").strip())
            except:
                pass
        elif line.startswith("TENSION_CURVE:"):
            curve = line.replace("TENSION_CURVE:", "").strip()
            skeleton["structure"]["tension_curve"] = [float(x) for x in curve.replace(",", " ").split() if x.replace(".","").replace("-","").isdigit()]
        elif line.startswith("BEATS:"):
            beats_str = line.replace("BEATS:", "").strip()
            # Parse beats like "1. xxx 2. xxx 3. xxx"
            parts = re.split(r'\d+\.\s*', beats_str)
            for i, part in enumerate(parts[1:], 1):
                part = part.strip()
                if part:
                    # Split name and desc
                    skeleton["structure"]["beats"].append({
                        "id": i,
                        "name": f"beat_{i}",
                        "desc": part[:100]
                    })
    
    # Validate
    if skeleton["structure"]["beats"] or skeleton["genre"]:
        return skeleton
    return None

def load_raw_novels() -> List[Dict]:
    novels = []
    for f in RAW_DIR.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                novels.extend(data if isinstance(data, list) else [data])
        except Exception as e:
            print(f"Error loading {f}: {e}")
    return novels

def save_skeleton(skeleton: Dict):
    # Filter out bad quality skeletons
    title = skeleton.get('title', '')
    # Skip if title is empty, placeholder, or invalid
    if not title or title in ['unknown', 'Unknown', '无标题', '无法提取', '[未提供]', '-']:
        return
    
    # Skip if title contains invalid characters
    if title.startswith('(') or title.startswith('[') or title.startswith('-'):
        return
    
    lang = skeleton.get('language', 'unknown')
    lang_dir = SKELETON_DIR / lang
    lang_dir.mkdir(parents=True, exist_ok=True)
    
    safe_title = skeleton.get('title', 'unknown').replace('/', '_')[:40]
    filename = lang_dir / f"{safe_title}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(skeleton, f, ensure_ascii=False, indent=2)

def get_progress() -> Dict:
    stats = {"total": 0, "by_language": {}}
    for f in SKELETON_DIR.rglob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                lang = data.get('language', 'unknown')
                stats["by_language"][lang] = stats["by_language"].get(lang, 0) + 1
                stats["total"] += 1
        except:
            pass
    return stats

def run_pipeline(batch_size: int = 10):
    print(f"=== Pipeline: {MODEL} ===")
    
    novels = load_raw_novels()
    print(f"Raw: {len(novels)}")
    
    progress = get_progress()
    print(f"Current: {progress['total']} ({progress['by_language']})")
    
    extracted = 0
    for i, novel in enumerate(novels[:batch_size]):
        title = novel.get('title', f'novel_{i}')
        text = novel.get('plot', '') or novel.get('text', '') or novel.get('content', '')
        
        if not text:
            continue
        
        print(f"[{i+1}/{batch_size}] {title[:30]}...", end=" ")
        
        skeleton = extract_skeleton(text, title)
        
        if skeleton:
            save_skeleton(skeleton)
            extracted += 1
            print(f"✓ {skeleton.get('language')}")
        else:
            print("✗")
        
        time.sleep(0.5)
    
    progress = get_progress()
    print(f"\nDone: {extracted}/{batch_size}")
    print(f"Total: {progress['total']} ({progress['by_language']})")
    
    return extracted

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", "-b", type=int, default=10)
    run_pipeline(parser.parse_args().batch)
