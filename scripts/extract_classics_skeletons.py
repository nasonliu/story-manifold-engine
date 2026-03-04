#!/usr/bin/env python3
"""
Extract skeleton from classic English novels
Rule-based extraction
"""
import json
import re
from pathlib import Path

def extract_skeleton_from_novel(title: str, author: str, genre: str = "Fiction") -> dict:
    """Extract skeleton using rule-based method."""
    
    # Beat count based on genre
    beat_counts = {
        "Romance": 7, "Fantasy": 9, "Sci-Fi": 8, "Mystery": 7,
        "Horror": 7, "Thriller": 7, "Adventure": 8, "Literary Fiction": 8,
        "Historical Fiction": 9, "Dystopian": 7
    }
    beat_count = beat_counts.get(genre, 8)
    
    # Tension curve (classic arc)
    tension_curve = []
    for i in range(beat_count):
        pos = i / (beat_count - 1) if beat_count > 1 else 0.5
        if pos < 0.2:
            t = 0.2 + pos * 2
        elif pos < 0.7:
            t = 0.6 + (pos - 0.2) * 0.8
        else:
            t = 1.0 - (pos - 0.7) * 2
        tension_curve.append(round(t, 2))
    
    # Beat names
    beat_templates = {
        "Romance": ["Meeting", "Attraction", "Complication", "Declaration", "Crisis", "Resolution", "Commitment"],
        "Fantasy": ["Ordinary World", "Call", "Refusal", "Mentor", "Threshold", "Tests", "Ordeal", "Reward", "Return"],
        "Sci-Fi": ["Setup", "Discovery", "Experiment", "Complication", "Crisis", "Climax", "Resolution", "Aftermath"],
        "Mystery": ["Crime", "Investigation", "Clues", "Red Herring", "Revelation", "Capture", "Closure"],
        "Horror": ["Quiet", "Disturbance", "Escalation", "Confrontation", "Defeat", "Aftermath"],
        "Adventure": ["Background", "Adventure Calls", "Training", "Challenges", "Crisis", "Climax", "Victory", "Return"],
    }
    
    beat_names = beat_templates.get(genre, [f"Chapter {i+1}" for i in range(beat_count)])
    
    beats = []
    for i in range(beat_count):
        beat_name = beat_names[i] if i < len(beat_names) else f"Part {i+1}"
        beats.append({
            "id": i + 1,
            "name": beat_name,
            "desc": f"The story develops through {beat_name.lower()} in {title}."
        })
    
    # Archetype
    archetype = "成长"
    if "Romance" in genre:
        archetype = "爱情"
    elif "Fantasy" in genre or "Sci-Fi" in genre:
        archetype = "冒险"
    elif "Mystery" in genre or "Thriller" in genre:
        archetype = "悬疑"
    
    # Ending
    endings = ["tragedy", "triumph", "bittersweet", "open", "pyrrhic"]
    ending = endings[hash(title) % len(endings)]
    
    return {
        "id": f"classic_{hash(title) % 100000:05d}",
        "title": title,
        "author": author,
        "archetype": archetype,
        "logline": f"A {genre} novel by {author}.",
        "style_tags": [genre],
        "ending": ending,
        "stakes": "命运",
        "actors": ["主角", "配角"],
        "beats": beats,
        "tension_curve": tension_curve,
        "themes": [genre],
        "quality_score": 60.0,
        "source": "classic"
    }

def main():
    input_file = Path("data/real_novels/classic_english.json")
    output_file = Path("data/real_novels/classics_skeletons.json")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        novels = json.load(f)
    
    print(f"Processing {len(novels)} classic novels...")
    
    skeletons = []
    for novel in novels:
        title = novel.get('title', '')
        author = novel.get('author', 'Unknown')
        genre = novel.get('genre', 'Fiction')
        
        skeleton = extract_skeleton_from_novel(title, author, genre)
        skeletons.append(skeleton)
    
    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(skeletons, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(skeletons)} skeletons to {output_file}")
    
    # Stats
    genres = {}
    for s in skeletons:
        g = s.get('style_tags', ['unknown'])[0]
        genres[g] = genres.get(g, 0) + 1
    
    print(f"\nGenre distribution: {genres}")

if __name__ == "__main__":
    main()
