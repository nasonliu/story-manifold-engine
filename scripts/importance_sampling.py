#!/usr/bin/env python3
"""
Importance Sampling: 能量驱动 + 多样性约束
p_train = 0.7 * p_classic + 0.3 * p_uniform
"""
import json, random, argparse
import numpy as np
from pathlib import Path
from sklearn.neighbors import KernelDensity, NearestNeighbors
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
from encoder.text_utils import skeleton_to_dsl
from collections import Counter


def compute_energy(emb, center):
    """能量函数：到 known_works 中心的距离"""
    return np.linalg.norm(emb - center)


def compute_pc1_penalty(emb, pca, scaler):
    """PC1 正向惩罚：过于现代/实验的叙事"""
    emb_scaled = scaler.transform(emb.reshape(1, -1))
    pc1 = pca.transform(emb_scaled)[0, 0]
    return max(0, pc1)  # 只惩罚正向（现代端）


def sample_with_constraints(skeletons, embs, kw_center, pca, scaler, 
                           n_select, alpha=0.5, beta=0.3,
                           max_archetype_ratio=0.15, max_ending_ratio=0.20):
    """
    重要性采样 + 多样性约束
    """
    n = len(skeletons)
    
    # 计算能量和PC1
    energies = np.array([compute_energy(e, kw_center) for e in embs])
    pc1_penalties = np.array([compute_pc1_penalty(e, pca, scaler) for e in embs])
    
    # 归一化
    energies_norm = (energies - energies.min()) / (energies.max() - energies.min() + 1e-8)
    pc1_norm = (pc1_penalties - pc1_penalties.min()) / (pc1_penalties.max() - pc1_penalties.min() + 1e-8)
    
    # 采样分数
    scores = np.exp(-alpha * energies_norm) * np.exp(-beta * pc1_norm)
    
    # 多样性约束：按 archetype 和 ending 分层采样
    archetypes = [s.get('archetype', '') for s in skeletons]
    endings = [s.get('ending', '') for s in skeletons]
    
    # 按分数排序
    sorted_idx = np.argsort(-scores)
    
    selected = []
    archetype_counts = Counter()
    ending_counts = Counter()
    
    for idx in sorted_idx:
        if len(selected) >= n_select:
            break
        
        arch = archetypes[idx]
        end = endings[idx]
        
        # 检查约束
        if archetype_counts[arch] / n_select >= max_archetype_ratio:
            continue
        if ending_counts[end] / n_select >= max_ending_ratio:
            continue
        
        selected.append(idx)
        archetype_counts[arch] += 1
        ending_counts[end] += 1
    
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/cleaned_skeletons/skeletons_v2.json")
    parser.add_argument("--output", default="data/sampled_skeletons/sampled_v1.json")
    parser.add_argument("--n", type=int, default=1000, help="采样数量")
    parser.add_argument("--alpha", type=float, default=0.5, help="能量权重")
    parser.add_argument("--beta", type=float, default=0.3, help="PC1权重")
    args = parser.parse_args()
    
    print("=== Loading data ===")
    p = Path(args.input)
    skeletons = json.loads(p.read_text())
    print(f"Total: {len(skeletons)}")
    
    print("\n=== Loading known_works ===")
    kw_files = sorted(Path("data/raw_skeletons_known/batch_1k").glob("wk_*.json"))
    known_works = [json.loads(f.read_text()) for f in kw_files]
    
    print("\n=== Encoding ===")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    sk_texts = [skeleton_to_dsl(s) for s in skeletons]
    sk_embs = model.encode(sk_texts, show_progress_bar=True)
    
    kw_texts = [skeleton_to_dsl(s) for s in known_works]
    kw_embs = model.encode(kw_texts, show_progress_bar=True)
    
    # 计算 known_works 中心
    kw_center = np.mean(kw_embs, axis=0)
    
    # PCA for PC1
    all_embs = np.vstack([sk_embs, kw_embs])
    scaler = StandardScaler()
    all_scaled = scaler.fit_transform(all_embs)
    pca = PCA(n_components=5)
    pca.fit(all_scaled)
    
    print("\n=== Importance Sampling ===")
    selected_idx = sample_with_constraints(
        skeletons, sk_embs, kw_center, pca, scaler,
        n_select=args.n, alpha=args.alpha, beta=args.beta
    )
    
    selected = [skeletons[i] for i in selected_idx]
    
    # 保存
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(selected, ensure_ascii=False, indent=2))
    print(f"\nSaved: {args.output}")
    print(f"Selected: {len(selected)}")
    
    # 统计
    archs = Counter(s.get('archetype', '') for s in selected)
    ends = Counter(s.get('ending', '') for s in selected)
    print(f"\nTop archetypes: {archs.most_common(5)}")
    print(f"Top endings: {ends.most_common()}")


if __name__ == "__main__":
    main()
