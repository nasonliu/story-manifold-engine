#!/usr/bin/env python3
"""
Story Manifold 可视化 + 聚类
用法：python visualize.py
输出：data/story_map.html（交互式地图）

需要安装：
pip install umap-learn hdbscan plotly sentence-transformers
"""
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import umap
import hdbscan
import plotly.express as px
import pandas as pd

SKELETONS_FILE = Path("data/cleaned_skeletons/skeletons.json")
ENCODER_PATH = Path("encoder/story-encoder-zh")
OUT_HTML = Path("data/story_map.html")
OUT_EMBEDDINGS = Path("data/embeddings/story_vectors.npy")

def skeleton_to_text(sk: dict) -> str:
    beats = sk.get("beats", [])
    archetype = "、".join(sk.get("archetype", []))
    events = " → ".join(b["event"] for b in beats)
    return f"【{archetype}】{events}"

def main():
    print("Loading skeletons...")
    with open(SKELETONS_FILE) as f:
        skeletons = json.load(f)

    texts = [skeleton_to_text(sk) for sk in skeletons]
    labels = ["/".join(sk["archetype"]) for sk in skeletons]
    endings = [sk.get("ending", "") for sk in skeletons]
    ids = [sk["id"] for sk in skeletons]

    print(f"Encoding {len(texts)} skeletons...")
    model = SentenceTransformer(str(ENCODER_PATH))
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    OUT_EMBEDDINGS.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUT_EMBEDDINGS, embeddings)
    print(f"Saved embeddings → {OUT_EMBEDDINGS}")

    print("UMAP dimensionality reduction...")
    reducer = umap.UMAP(n_components=2, random_state=42, min_dist=0.1, n_neighbors=15)
    coords = reducer.fit_transform(embeddings)

    print("HDBSCAN clustering...")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=3)
    cluster_labels = clusterer.fit_predict(embeddings)
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    print(f"Found {n_clusters} clusters")

    df = pd.DataFrame({
        "x": coords[:, 0],
        "y": coords[:, 1],
        "id": ids,
        "archetype": labels,
        "ending": endings,
        "cluster": [f"C{c}" if c >= 0 else "noise" for c in cluster_labels],
        "hover": [skeleton_to_text(sk)[:80] + "..." for sk in skeletons],
    })

    fig = px.scatter(
        df, x="x", y="y",
        color="cluster",
        hover_name="id",
        hover_data={"archetype": True, "ending": True, "hover": True, "x": False, "y": False},
        title="Story Manifold Map",
        width=1200, height=800,
    )
    fig.write_html(str(OUT_HTML))
    print(f"\n✅ Story Map saved → {OUT_HTML}")
    print("Open in browser to explore!")

if __name__ == "__main__":
    main()
