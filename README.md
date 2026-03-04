# Story Manifold Engine

> 从大模型蒸馏叙事结构，构建故事潜空间。

## 项目目标

不是 AI 写作工具，而是**叙事操作系统**：

- 学习故事结构的低维潜空间（Story Manifold）
- 支持：相似故事检索 / 结构混合 / 新骨架生成
- 为 IP 生产、短剧创作、游戏叙事提供结构引擎

## 核心发现：叙事物理学

通过 Narrative Physics 实验，我们发现：

### 1. 结构吸引子存在
- 使用 12 维结构参数（L, C, R, Tshape, I, Delay, K, Cross, Agency, Closure）
- 真实文学作品在该参数空间中表现为**稳定的低密度区域**
- 99.9% 的合成样本比真实文学更密集

### 2. 阈值不变性
- 无论使用 p30、p50 还是 p70 作为阈值
- known_works 的 above-threshold 比例始终为 **0%**
- 结论对阈值选择完全鲁棒

### 3. 关键结论
> 真实文学结构位于 NP 合成数据覆盖较少的"创意区域"，而非高密核心。这表明叙事结构存在自然规律，但真实文学往往突破这些"典型"模式。

## Real Novel Dataset

Current skeleton count: **64**

Language distribution:
- Chinese web novels: 63 (98.4%)
- English: 1 (1.6%)
- Classic literature: 0
- Other languages: 0

Target ratio:
- Chinese web novels <=35%
- English 40%
- Classic literature 15%
- Other languages 10%

## Clustering results

- Cluster count proxy (genre buckets): pending full UMAP/HDBSCAN
- Silhouette: pending
- Davies-Bouldin: pending

## Synthetic vs real analysis

Current observation:
- Synthetic skeletons are highly uniform in archetype and beat count.
- Real extraction (local deepseek-r1:8b) shows early diversity but currently zh-heavy.
- Next step is balancing source/language mix while scaling to 2000 (Phase 1).

## 目录结构

```
story-engine/
├── data/
│   ├── raw_skeletons/
│   ├── cleaned_skeletons/
│   ├── narrative_physics/
│   ├── embeddings/
│   ├── real_novels_raw/
│   └── real_novels_skeletons/
├── scripts/
│   ├── novel_pipeline.py
│   ├── extract_skeleton.py
│   ├── dataset_balance.py
│   └── run_clustering.py
└── docs/plans/
```
