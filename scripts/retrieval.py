#!/usr/bin/env python3
"""
Skeleton Retrieval System
- Textifies skeletons for embedding
- Builds FAISS index
- Provides filtered search
"""
import json, glob, pickle, os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Config
DATA_DIR = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/cleaned_skeletons')
MODEL_NAME = 'BAAI/bge-base-zh-v1.5'
INDEX_DIR = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/index')
INDEX_FILE = INDEX_DIR / 'skeletons_v2.index'
META_FILE = INDEX_DIR / 'skeletons_v2_meta.pkl'

# Ensure index dir exists
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def beat_text(b: dict) -> str:
    """Convert beat to text for embedding."""
    name = (b.get('name') or '').strip()
    desc = (b.get('desc') or '').strip()
    return f"{name}。{desc}" if name or desc else ''

def skeleton_to_text(sk: dict) -> str:
    """Convert full skeleton to text for semantic search."""
    parts = []
    
    # Archetype
    archetype = sk.get('archetype', '')
    if archetype:
        parts.append(f"原型:{archetype}")
    
    # Title & Logline
    title = sk.get('title', '')
    logline = sk.get('logline', '')
    if title:
        parts.append(f"标题:{title}")
    if logline:
        parts.append(f"概要:{logline}")
    
    # Beats
    beats = sk.get('beats', [])
    if beats:
        beat_texts = [beat_text(b) for b in beats]
        beat_texts = [t for t in beat_texts if t]
        if beat_texts:
            parts.append("情节:" + " ".join(beat_texts[:6]))  # Limit to first 6 beats
    
    # Themes
    themes = sk.get('themes', [])
    if themes:
        parts.append(f"主题:{','.join(themes)}")
    
    # Style tags
    style_tags = sk.get('style_tags', [])
    if style_tags:
        parts.append(f"风格:{','.join(style_tags)}")
    
    return " ".join(parts)

def load_skeletons() -> List[dict]:
    """Load all cleaned skeletons."""
    skeleton_file = DATA_DIR / 'skeletons_v2.json'
    with open(skeleton_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_index(force: bool = False):
    """Build FAISS index from skeletons."""
    if INDEX_FILE.exists() and META_FILE.exists() and not force:
        print(f"Index already exists at {INDEX_FILE}")
        return
    
    print("Loading skeletons...")
    skeletons = load_skeletons()
    print(f"Loaded {len(skeletons)} skeletons")
    
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    
    print("Converting to text...")
    texts = [skeleton_to_text(sk) for sk in skeletons]
    
    print(f"Encoding {len(texts)} texts...")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    embeddings = embeddings.astype('float32')
    
    print(f"Building FAISS index (dim={embeddings.shape[1]})...")
    index = faiss.IndexFlatIP(embeddings.shape[1])  # Inner product for cosine sim
    index.add(embeddings)
    
    print("Saving index...")
    faiss.write_index(index, str(INDEX_FILE))
    
    # Save metadata
    meta = {
        'skeletons': skeletons,
        'texts': texts,
        'model': MODEL_NAME,
    }
    with open(META_FILE, 'wb') as f:
        pickle.dump(meta, f)
    
    print(f"Index built: {len(skeletons)} vectors, dim={embeddings.shape[1]}")

def search(
    query: str,
    k: int = 10,
    archetype: Optional[str] = None,
    ending: Optional[str] = None,
    style_tags: Optional[List[str]] = None,
) -> List[Tuple[dict, float]]:
    """
    Search skeletons by query text with optional filters.
    
    Args:
        query: Semantic search query
        k: Number of results
        archetype: Filter by archetype (exact match)
        ending: Filter by ending type
        style_tags: Filter by style tags (any match)
    
    Returns:
        List of (skeleton, score) tuples
    """
    # Load index
    if not INDEX_FILE.exists():
        build_index()
    
    index = faiss.read_index(str(INDEX_FILE))
    with open(META_FILE, 'rb') as f:
        meta = pickle.load(f)
    
    skeletons = meta['skeletons']
    texts = meta['texts']
    
    # Encode query
    model = SentenceTransformer(MODEL_NAME)
    query_vec = model.encode([query], normalize_embeddings=True).astype('float32')
    
    # Search
    scores, indices = index.search(query_vec, k * 10)  # Oversearch for filtering
    scores = scores[0]
    indices = indices[0]
    
    # Apply filters
    results = []
    for idx, score in zip(indices, scores):
        if idx < 0:
            continue
        sk = skeletons[idx]
        
        # Filter by archetype
        if archetype and sk.get('archetype') != archetype:
            continue
        
        # Filter by ending
        if ending and sk.get('ending') != ending:
            continue
        
        # Filter by style_tags
        if style_tags:
            sk_tags = set(sk.get('style_tags', []))
            if not sk_tags.intersection(set(style_tags)):
                continue
        
        results.append((sk, float(score)))
        
        if len(results) >= k:
            break
    
    return results

def search_cli():
    """CLI for searching."""
    import argparse
    parser = argparse.ArgumentParser(description='Search skeletons')
    parser.add_argument('query', nargs='?', default='复仇 悬疑')
    parser.add_argument('-k', '--top-k', type=int, default=5)
    parser.add_argument('--archetype', type=str, default=None)
    parser.add_argument('--ending', type=str, default=None)
    parser.add_argument('--style', type=str, default=None)
    args = parser.parse_args()
    
    style_tags = args.style.split(',') if args.style else None
    
    results = search(
        args.query,
        k=args.top_k,
        archetype=args.archetype,
        ending=args.ending,
        style_tags=style_tags,
    )
    
    print(f"\n=== Top {len(results)} Results ===")
    for sk, score in results:
        print(f"\n[{score:.3f}] {sk.get('title')} (ID: {sk.get('id')})")
        print(f"  Archetype: {sk.get('archetype')} | Ending: {sk.get('ending')}")
        print(f"  Logline: {sk.get('logline', '')[:80]}...")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        search_cli()
    else:
        # Build index
        build_index()
        print("Index ready. Run with query to search.")
