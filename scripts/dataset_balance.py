#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/real_novels_skeletons')

def source_bucket(d):
    lang = (d.get('language') or '').lower()
    genre = (d.get('genre') or '').lower()
    if lang.startswith('zh'):
        return 'chinese_web'
    if lang.startswith('en') and ('classic' not in genre):
        return 'english'
    if 'classic' in genre:
        return 'classic_lit'
    return 'other'

counts = {'chinese_web':0,'english':0,'classic_lit':0,'other':0}
total=0
for f in ROOT.rglob('*.json'):
    try:
        d=json.loads(f.read_text())
        b=source_bucket(d)
        counts[b]+=1
        total+=1
    except: pass

ratios={k:(v/total if total else 0) for k,v in counts.items()}
print({'total':total,'counts':counts,'ratios':ratios})
