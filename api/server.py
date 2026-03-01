#!/usr/bin/env python3
"""
Story Engine API
用法：uvicorn server:app --reload

需要安装：
pip install fastapi uvicorn sentence-transformers faiss-cpu numpy
"""
import json
import numpy as np
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import faiss

SKELETONS_FILE = Path("data/cleaned_skeletons/skeletons.json")
EMBEDDINGS_FILE = Path("data/embeddings/story_vectors.npy")
ENCODER_PATH = Path("encoder/story-encoder-zh")

app = FastAPI(title="Story Engine API")

# Global state
skeletons = []
embeddings = None
index = None
model = None

@app.on_event("startup")
def load_data():
    global skeletons, embeddings, index, model
    with open(SKELETONS_FILE) as f:
        skeletons = json.load(f)
    embeddings = np.load(EMBEDDINGS_FILE).astype("float32")
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    model = SentenceTransformer(str(ENCODER_PATH))
    print(f"Loaded {len(skeletons)} skeletons, dim={embeddings.shape[1]}")

def skeleton_to_text(sk):
    beats = sk.get("beats", [])
    archetype = "、".join(sk.get("archetype", []))
    events = " → ".join(b["event"] for b in beats)
    return f"【{archetype}】{events}"

class SearchRequest(BaseModel):
    text: str
    top_k: int = 10

class MixRequest(BaseModel):
    id_a: str
    id_b: str
    alpha: float = 0.5  # 0=全A，1=全B
    top_k: int = 5

@app.post("/search")
def search(req: SearchRequest):
    vec = model.encode([req.text], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(vec, req.top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        sk = skeletons[idx]
        results.append({
            "id": sk["id"],
            "archetype": sk["archetype"],
            "ending": sk["ending"],
            "similarity": float(score),
            "beats": [b["event"] for b in sk["beats"]],
        })
    return {"query": req.text, "results": results}

@app.post("/mix")
def mix(req: MixRequest):
    id_map = {sk["id"]: i for i, sk in enumerate(skeletons)}
    if req.id_a not in id_map or req.id_b not in id_map:
        return {"error": "ID not found"}
    va = embeddings[id_map[req.id_a]]
    vb = embeddings[id_map[req.id_b]]
    mixed = (1 - req.alpha) * va + req.alpha * vb
    mixed = mixed / np.linalg.norm(mixed)
    mixed = mixed.reshape(1, -1).astype("float32")
    scores, indices = index.search(mixed, req.top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        sk = skeletons[idx]
        results.append({
            "id": sk["id"],
            "archetype": sk["archetype"],
            "ending": sk["ending"],
            "similarity": float(score),
            "beats": [b["event"] for b in sk["beats"]],
        })
    return {"id_a": req.id_a, "id_b": req.id_b, "alpha": req.alpha, "results": results}

@app.get("/skeleton/{skeleton_id}")
def get_skeleton(skeleton_id: str):
    for sk in skeletons:
        if sk["id"] == skeleton_id:
            return sk
    return {"error": "Not found"}

@app.get("/stats")
def stats():
    from collections import Counter
    archetypes = [a for sk in skeletons for a in sk["archetype"]]
    endings = [sk["ending"] for sk in skeletons]
    return {
        "total": len(skeletons),
        "archetypes": dict(Counter(archetypes).most_common(20)),
        "endings": dict(Counter(endings)),
    }
