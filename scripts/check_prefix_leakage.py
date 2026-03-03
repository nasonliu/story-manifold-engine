#!/usr/bin/env python3
"""
Sanity check for prefix leakage detection.
Three tests:
A. Remove archetype prefix, re-cluster
B. Shuffle archetype labels, check if clusters still follow theme
C. Embed archetype only, compare with full embedding clusters
"""
import json, random, argparse
from collections import Counter
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
import numpy as np

# Use the new anti-leakage text utils
from encoder.text_utils import skeleton_to_dsl, skeleton_to_structure_only


def load_skeletons(n=1000):
    """Load skeletons from cleaned data."""
    p = Path("data/cleaned_skeletons/skeletons_v2.json")
    if not p.exists():
        p = Path("data/raw_skeletons")
        files = sorted(p.glob("sk_*.json"))[:n]
        return [json.loads(f.read_text()) for f in files]
    data = json.loads(p.read_text())
    return data[:n]


def quick_embed_texts(texts, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
    """Quick embedding using sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return model.encode(texts, show_progress_bar=False)


def test_A_no_archetype(skeletons, n_clusters=20):
    """
    Test A: Remove archetype, keep only beats.
    If clustering drops significantly -> was relying on prefix.
    """
    print("\n=== Test A: No Archetype (beats only) ===")
    
    # Original with archetype
    texts_orig = [skeleton_to_dsl(s) for s in skeletons]
    emb_orig = quick_embed_texts(texts_orig)
    
    # Without archetype
    texts_no_arch = [skeleton_to_structure_only(s) for s in skeletons]
    emb_no_arch = quick_embed_texts(texts_no_arch)
    
    # Cluster both
    labels_orig = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(emb_orig)
    labels_no_arch = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(emb_no_arch)
    
    # Compare with archetype labels
    archetype_labels = [s.get('archetype', '') for s in skeletons]
    arch_unique = list(set(archetype_labels))
    arch_to_id = {a: i for i, a in enumerate(arch_unique)}
    true_labels = [arch_to_id.get(a, 0) for a in archetype_labels]
    
    ari_orig = adjusted_rand_score(true_labels, labels_orig)
    ari_no_arch = adjusted_rand_score(true_labels, labels_no_arch)
    
    print(f"  Original (with archetype) vs archetype labels ARI: {ari_orig:.3f}")
    print(f"  No archetype vs archetype labels ARI: {ari_no_arch:.3f}")
    print(f"  Delta: {ari_no_arch - ari_orig:.3f} ({'SIGNIFICANT DROP' if (ari_no_arch - ari_orig) < -0.1 else 'OK'})")
    
    return ari_orig, ari_no_arch


def test_B_shuffle_archetype(skeletons, n_clusters=20):
    """
    Test B: Shuffle archetype labels randomly.
    If clusters still follow original archetype -> was relying on prefix.
    """
    print("\n=== Test B: Shuffled Archetype Labels ===")
    
    # Get texts
    texts = [skeleton_to_dsl(s) for s in skeletons]
    emb = quick_embed_texts(texts)
    
    # True archetype labels
    archetype_labels = [s.get('archetype', '') for s in skeletons]
    arch_unique = list(set(archetype_labels))
    arch_to_id = {a: i for i, a in enumerate(arch_unique)}
    true_labels = [arch_to_id.get(a, 0) for a in archetype_labels]
    
    # Cluster original embeddings
    labels_orig = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(emb)
    ari_true = adjusted_rand_score(true_labels, labels_orig)
    
    # Shuffle archetypes
    archetypes = [s.get('archetype', '') for s in skeletons]
    shuffled = archetypes.copy()
    random.seed(42)
    random.shuffle(shuffled)
    
    # Now compare shuffled archetype vs clusters
    shuffled_labels = [arch_to_id.get(a, 0) for a in shuffled]
    ari_shuffled = adjusted_rand_score(shuffled_labels, labels_orig)
    
    print(f"  True archetype vs clusters ARI: {ari_true:.3f}")
    print(f"  Shuffled archetype vs clusters ARI: {ari_shuffled:.3f}")
    print(f"  If clusters still match shuffled -> PREFIX LEAKAGE")
    print(f"  Interpretation: {'LEAKAGE DETECTED' if ari_shuffled > 0.3 else 'CLEAN'}")
    
    return ari_true, ari_shuffled


def test_C_archetype_only(skeletons, n_clusters=20):
    """
    Test C: Embed archetype only.
    If similar to full embedding clusters -> prefix dominates.
    """
    print("\n=== Test C: Archetype Only vs Full ===")
    
    # Full embedding
    texts_full = [skeleton_to_dsl(s) for s in skeletons]
    emb_full = quick_embed_texts(texts_full)
    
    # Archetype only
    texts_arch = [s.get('archetype', '') for s in skeletons]
    emb_arch = quick_embed_texts(texts_arch)
    
    # Cluster both
    labels_full = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(emb_full)
    labels_arch = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(emb_arch)
    
    # Compare
    ari = adjusted_rand_score(labels_full, labels_arch)
    
    print(f"  Full text clusters vs archetype-only clusters ARI: {ari:.3f}")
    print(f"  Interpretation: {'HIGH CORRELATION - PREFIX DOMINATES' if ari > 0.5 else 'OK'}")
    
    return ari


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500, help="Number of skeletons to test")
    parser.add_argument("--clusters", type=int, default=20, help="Number of clusters")
    args = parser.parse_args()
    
    print(f"Loading {args.n} skeletons...")
    skeletons = load_skeletons(args.n)
    print(f"Loaded {len(skeletons)} skeletons")
    
    # Run tests
    ari_orig, ari_no_arch = test_A_no_archetype(skeletons, args.clusters)
    ari_true, ari_shuffled = test_B_shuffle_archetype(skeletons, args.clusters)
    ari_arch_only = test_C_archetype_only(skeletons, args.clusters)
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    issues = []
    if ari_no_arch - ari_orig < -0.1:
        issues.append("Test A: Significant drop without archetype -> PREFIX LEAKAGE")
    if ari_shuffled > 0.3:
        issues.append("Test B: Clusters still match shuffled labels -> PREFIX LEAKAGE")
    if ari_arch_only > 0.5:
        issues.append("Test C: Archetype dominates clustering -> PREFIX LEAKAGE")
    
    if issues:
        print("ISSUES DETECTED:")
        for i in issues:
            print(f"  - {i}")
        print("\nRECOMMENDATION: Use skeleton_to_structure_only() or skeleton_to_dsl() for training")
    else:
        print("No prefix leakage detected - embeddings look clean!")


if __name__ == "__main__":
    main()
