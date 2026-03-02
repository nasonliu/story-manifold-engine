#!/usr/bin/env python3
import json, glob, random, time
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

RAW = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/raw_skeletons')
MODEL = 'BAAI/bge-base-zh-v1.5'
SAMPLE_N = 300
SEED = 42

def beat_text(b):
    name = (b.get('name') or '').strip()
    desc = (b.get('desc') or '').strip()
    return f"{name}。{desc}" if name or desc else ''

def load_samples(n):
    files = sorted(glob.glob(str(RAW / 'sk_*.json')))
    random.seed(SEED)
    files = random.sample(files, min(n, len(files)))
    samples = []
    for f in files:
        try:
            d = json.load(open(f, encoding='utf-8'))
            beats = d.get('beats') or []
            tc = d.get('tension_curve') or []
            if not isinstance(beats, list) or len(beats) == 0:
                continue
            bt = [beat_text(b) for b in beats]
            bt = [x for x in bt if x]
            if not bt:
                continue
            if not isinstance(tc, list) or len(tc) != len(beats):
                w = [1.0] * len(bt)
            else:
                w = [float(tc[i]) for i,b in enumerate(beats) if beat_text(b)]
                if not w:
                    w = [1.0] * len(bt)
            samples.append((d.get('id'), bt, w))
        except Exception:
            pass
    return samples

def weighted_pool(vectors, weights):
    W = np.array(weights, dtype=np.float32)
    W = np.clip(W, 1e-3, None)
    W = W / W.sum()
    V = np.array(vectors, dtype=np.float32)
    return (V * W[:, None]).sum(axis=0)

def main():
    t0 = time.time()
    samples = load_samples(SAMPLE_N)
    t1 = time.time()

    model = SentenceTransformer(MODEL)
    t2 = time.time()

    total_beats = sum(len(x[1]) for x in samples)
    beat_texts = [t for _, bt, _ in samples for t in bt]

    e0 = time.time()
    embs = model.encode(beat_texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    e1 = time.time()

    idx = 0
    for _, bt, w in samples:
        k = len(bt)
        _ = weighted_pool(embs[idx: idx + k], w)
        idx += k
    e2 = time.time()

    print(f'samples={len(samples)} total_beats={total_beats}')
    print(f'load_data_sec={t1-t0:.2f}')
    print(f'load_model_sec={t2-t1:.2f}')
    print(f'encode_beats_sec={e1-e0:.2f}')
    print(f'pooling_sec={e2-e1:.2f}')
    print(f'total_runtime_sec={e2-t0:.2f}')
    bps = total_beats/max(1e-6,(e1-e0))
    print(f'beats_per_sec={bps:.1f}')
    avg_beats = total_beats / max(1, len(samples))
    est_encode_sec = (10000 * avg_beats) / max(1e-6, bps)
    print(f'est_avg_beats_per_story={avg_beats:.2f}')
    print(f'est_encode_time_for_10k_sec={est_encode_sec:.1f} (~{est_encode_sec/60:.1f} min)')

if __name__ == '__main__':
    main()
