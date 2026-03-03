#!/usr/bin/env python3
"""
Narrative Continuity Test Suite
Tests whether the structure embedding space is truly continuous/manifold-like,
or just discrete template clusters.

Tests:
1. Beat Order Perturbation - small changes should cause smooth movement
2. Structure Interpolation - mid-point should find reasonable "middle structures"
3. Local Intrinsic Dimension - check if space is piecewise low-dimensional
"""
import json, random, argparse, copy
import numpy as np
from pathlib import Path
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer
from encoder.text_utils import skeleton_to_dsl, skeleton_to_structure_only


def load_skeletons(n=500):
    p = Path("data/cleaned_skeletons/skeletons_v2.json")
    if p.exists():
        return json.loads(p.read_text())[:n]
    files = sorted(Path("data/raw_skeletons").glob("sk_*.json"))[:n]
    return [json.loads(f.read_text()) for f in files]


def perturb_beats_order(skeleton, n_swaps=1):
    """Swap n pairs of beats to create small structural perturbation."""
    sk = copy.deepcopy(skeleton)
    beats = sk.get('beats', [])
    if len(beats) < 3:
        return sk
    
    for _ in range(n_swaps):
        i, j = random.sample(range(len(beats)), 2)
        beats[i], beats[j] = beats[j], beats[i]
    sk['beats'] = beats
    return sk


def perturb_tension_curve(skeleton, delta=0.1):
    """Shift tension curve by delta (with clipping)."""
    sk = copy.deepcopy(skeleton)
    tc = sk.get('tension_curve', [])
    if not tc:
        return sk
    sk['tension_curve'] = [max(0, min(1, x + delta)) for x in tc]
    return sk


def local_intrinsic_dimension(embs, k=10):
    """Estimate local ID using TwoNN method."""
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=k+1)
    nn.fit(embs)
    dists, _ = nn.kneighbors(embs)
    
    # Use first and second neighbor distances
    mu = dists[:, 1] / dists[:, 2]
    mu = mu[np.isfinite(mu) & (mu > 0)]
    if len(mu) < 10:
        return np.nan
    
    # ID estimate: -1 / log(mean(mu))
    with np.errstate(divide='ignore'):
        id_est = -1 / np.log(np.mean(mu))
    return id_est


def test_1_beat_perturbation(skeletons, model, n_test=50):
    """
    Test 1: Beat Order Perturbation
    Small structural changes should cause smooth embedding movement,
    not jump to another cluster.
    """
    print("\n=== Test 1: Beat Order Perturbation ===")
    
    # Select diverse samples
    indices = random.sample(range(len(skeletons)), min(n_test, len(skeletons)))
    
    original_embs = []
    perturbed_embs = []
    cluster_jumps = 0
    
    for idx in indices:
        sk = skeletons[idx]
        
        # Original
        text_orig = skeleton_to_dsl(sk)
        emb_orig = model.encode([text_orig], show_progress_bar=False)[0]
        
        # Perturbed (swap 1-2 beats)
        sk_pert = perturb_beats_order(sk, n_swaps=random.randint(1, 2))
        text_pert = skeleton_to_dsl(sk_pert)
        emb_pert = model.encode([text_pert], show_progress_bar=False)[0]
        
        original_embs.append(emb_orig)
        perturbed_embs.append(emb_pert)
        
        # Check if moved far (beyond local neighborhood)
        dist = np.linalg.norm(emb_orig - emb_pert)
        
        # Compare with typical within-cluster distance (estimate from data)
        # If perturbation distance >> typical neighbor distance, it's a "jump"
        if dist > 5.0:  # heuristic threshold
            cluster_jumps += 1
    
    original_embs = np.array(original_embs)
    perturbed_embs = np.array(perturbed_embs)
    
    # Average perturbation distance
    avg_dist = np.mean(np.linalg.norm(original_embs - perturbed_embs, axis=1))
    jump_rate = cluster_jumps / n_test
    
    print(f"  Average perturbation distance: {avg_dist:.3f}")
    print(f"  Cluster jump rate: {jump_rate:.1%}")
    print(f"  Interpretation:")
    if jump_rate < 0.3:
        print("    ✅ LOW - Space is relatively smooth")
    else:
        print("    ⚠️  HIGH - Space may be discrete")
    
    return {"avg_dist": avg_dist, "jump_rate": jump_rate}


def test_2_interpolation(skeletons, model, n_test=30):
    """
    Test 2: Structure Interpolation
    Take two skeletons, interpolate their embeddings,
    find nearest neighbors. Should find reasonable "middle structures".
    """
    print("\n=== Test 2: Structure Interpolation ===")
    
    # Select two different archetypes
    archetypes = {}
    for i, sk in enumerate(skeletons):
        a = sk.get('archetype', 'Unknown')
        if a not in archetypes:
            archetypes[a] = []
        archetypes[a].append(i)
    
    # Pick pairs from different archetypes
    test_pairs = []
    arch_list = list(archetypes.keys())
    for _ in range(n_test):
        a1, a2 = random.sample(arch_list, 2)
        idx1 = random.choice(archetypes[a1])
        idx2 = random.choice(archetypes[a2])
        test_pairs.append((idx1, idx2))
    
    # Encode all skeletons
    texts = [skeleton_to_dsl(s) for s in skeletons]
    all_embs = model.encode(texts, show_progress_bar=True)
    
    valid_middles = 0
    for i1, i2 in test_pairs:
        emb1, emb2 = all_embs[i1], all_embs[i2]
        
        # Interpolate
        emb_mid = 0.5 * emb1 + 0.5 * emb2
        
        # Find nearest neighbors
        nn = NearestNeighbors(n_neighbors=5)
        nn.fit(all_embs)
        _, indices = nn.kneighbors([emb_mid])
        
        # Check if neighbors are from both archetypes (not just one)
        neighbor_archs = [skeletons[idx].get('archetype') for idx in indices[0]]
        orig_archs = [skeletons[i1].get('archetype'), skeletons[i2].get('archetype')]
        
        # Valid if neighbors include diverse archetypes
        unique_neighbor_archs = len(set(neighbor_archs))
        if unique_neighbor_archs >= 3:
            valid_middles += 1
    
    valid_rate = valid_middles / n_test
    print(f"  Valid interpolation rate: {valid_rate:.1%}")
    print(f"  Interpretation:")
    if valid_rate > 0.5:
        print("    ✅ SPACE IS CONTINUOUS - Can find middle structures")
    else:
        print("    ⚠️  SPACE MAY BE DISCRETE - Tends to collapse to archetypes")
    
    return {"valid_rate": valid_rate}


def test_3_local_id(skeletons, model, n_clusters=12):
    """
    Test 3: Local Intrinsic Dimension
    Check if different clusters have different IDs.
    """
    print("\n=== Test 3: Local Intrinsic Dimension ===")
    
    texts = [skeleton_to_dsl(s) for s in skeletons]
    embs = model.encode(texts, show_progress_bar=True)
    
    # Cluster
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(embs)
    
    # Compute local ID per cluster
    cluster_ids = []
    for c in range(n_clusters):
        mask = labels == c
        cluster_embs = embs[mask]
        if len(cluster_embs) < 20:
            continue
        lid = local_intrinsic_dimension(cluster_embs, k=min(10, len(cluster_embs)-1))
        cluster_ids.append(lid)
    
    cluster_ids = [x for x in cluster_ids if not np.isnan(x)]
    
    if cluster_ids:
        mean_id = np.mean(cluster_ids)
        std_id = np.std(cluster_ids)
        print(f"  Cluster-level local IDs: {[f'{x:.1f}' for x in cluster_ids]}")
        print(f"  Mean local ID: {mean_id:.2f} +/- {std_id:.2f}")
        
        # Overall ID
        overall_id = local_intrinsic_dimension(embs, k=15)
        print(f"  Overall local ID: {overall_id:.2f}")
        
        print(f"  Interpretation:")
        if std_id < 1.0 and mean_id > 3:
            print("    ✅ RELATIVELY UNIFORM - Space is manifold-like")
        elif std_id > 2:
            print("    ⚠️  PIECEWISE - Different clusters have different dimensionality")
        else:
            print("    ⚡ MODERATE - Some structure but not extreme")
        
        return {"mean_id": mean_id, "std_id": std_id, "overall_id": overall_id}
    
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500)
    args = parser.parse_args()
    
    print(f"Loading {args.n} skeletons...")
    skeletons = load_skeletons(args.n)
    
    print("Loading model...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    random.seed(42)
    np.random.seed(42)
    
    # Run tests
    r1 = test_1_beat_perturbation(skeletons, model, n_test=50)
    r2 = test_2_interpolation(skeletons, model, n_test=30)
    r3 = test_3_local_id(skeletons, model)
    
    # Summary
    print("\n" + "="*50)
    print("NARRATIVE CONTINUITY TEST SUMMARY")
    print("="*50)
    
    issues = []
    if r1.get("jump_rate", 1) > 0.5:
        issues.append("Beat perturbation causes cluster jumps - SPACE MAY BE DISCRETE")
    if r2.get("valid_rate", 0) < 0.3:
        issues.append("Interpolation rarely finds middle structures - SPACE TENDS TO COLLAPSE")
    if r3.get("std_id", 0) > 2:
        issues.append("High ID variance across clusters - PIECEWISE STRUCTURE")
    
    if issues:
        print("\nISSUES:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("\n✅ CONTINUITY TESTS PASSED - Space appears manifold-like")
    
    return {"perturbation": r1, "interpolation": r2, "local_id": r3}


if __name__ == "__main__":
    main()
