#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

ROOT = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/real_novels_skeletons')
rows=[]
for f in ROOT.rglob('*.json'):
    try:
        d=json.loads(f.read_text())
        rows.append(d)
    except: pass

genres=Counter((r.get('genre') or 'unknown') for r in rows)
langs=Counter((r.get('language') or 'unknown') for r in rows)
report = {
  'total': len(rows),
  'cluster_count_proxy': len(genres),
  'silhouette': None,
  'davies_bouldin': None,
  'language_distribution': dict(langs),
  'structure_distribution': dict(genres)
}
out=Path('/home/nason/.openclaw/workspace/story-manifold-engine/reports/clustering_progress.md')
out.write_text('# Clustering Progress\n\n```json\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n```\n')
print(report)
