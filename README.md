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

## 架构

```
Teacher LLM（生成骨架）
        ↓
Story Skeleton Dataset（JSON）
        ↓
Narrative Physics Generator
        ↓
Story Encoder（对比学习）
        ↓
Story Latent Space
        ↓
UMAP + HDBSCAN（可视化 & 聚类）
        ↓
Story Engine API（检索 / 混合 / 生成）
```

## 目录结构

```
story-engine/
├── data/
│   ├── raw_skeletons/      # 原始生成的骨架 JSON
│   ├── cleaned_skeletons/  # 清洗后的骨架
│   ├── narrative_physics/  # Narrative Physics 生成数据
│   └── embeddings/         # 向量文件
├── generator/
│   ├── clean_skeletons.py  # 清洗 & 去重
│   └── validator.py        # Schema 校验
├── encoder/
│   └── text_utils.py       # 向编码工具
├── scripts/
│   ├── generate_narrative_physics.py  # 核心生成器
│   ├── importance_sampling.py          # 重要性采样
│   ├── check_prefix_leakage.py        # 前缀泄漏检测
│   └── narrative_continuity_test.py    # 连续性测试
├── analysis/
│   └── visualize.py        # UMAP 可视化
├── api/
│   └── server.py           # FastAPI 服务
├── docs/plans/             # 实验计划与报告
└── requirements.txt
```

## Narrative Physics 参数空间

| 参数 | 范围 | 描述 |
|------|------|------|
| L | 3-15 | Beats 数量 |
| C | 0.4-0.9 | Climax 位置 |
| R | 0-3 | Reversals 数量 |
| Tshape | 5种 | 张力曲线类型 |
| I | 0-2 | 信息不对称程度 |
| Delay | 0-2 | 伏笔回收延迟 |
| K | 1-3 | 冲突源数量 |
| Cross | 0-2 | 冲突耦合度 |
| Agency | 0-2 | 主角能动性 |
| Closure | 0-2 | 结局闭合度 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成 Narrative Physics 数据

```bash
cd story-engine
python scripts/generate_narrative_physics.py --n 10000
```

### 3. 编码与评估

```bash
# 使用 skeleton_to_dsl_v2 进行编码
python -c "from encoder.text_utils import skeleton_to_dsl_v2; print(skeleton_to_dsl_v2(skeleton))"
```

### 4. 可视化

```bash
python analysis/visualize.py
# 打开 data/story_map.html
```

## Skeleton Schema (Narrative Physics)

```json
{
  "id": "sk_001",
  "archetype": "英雄成长",
  "beats": [
    {"role": "setup", "tension": 0.1, "info_delta": 0, "state_delta": "same"},
    {"role": "progress", "tension": 0.3, "info_delta": 0, "state_delta": "same"},
    {"role": "pressure", "tension": 0.6, "info_delta": -1, "state_delta": "same"},
    {"role": "climax", "tension": 1.0, "info_delta": 1, "state_delta": "goal_shift"},
    {"role": "resolution", "tension": 0.2, "info_delta": 0, "state_delta": "same"}
  ],
  "turning_points": [{"beat": 3, "type": "goal_shift"}],
  "climax_position": 0.75,
  "ending": "closed",
  "structure_params": {
    "L": 9,
    "C": 0.75,
    "R": 2,
    "Tshape": "hill",
    "I": 1,
    "Delay": 1,
    "K": 2,
    "Cross": 1,
    "Agency": 2,
    "Closure": 2
  }
}
```

## 实验报告

- [Phase 1 计划与进展](docs/plans/2026-03-02-a-plan-and-phase1.md)
- [前缀泄漏检测报告](reports/prefix_leakage_report.md)

## 路线图

- [x] Narrative Physics 生成器
- [x] 12 维结构参数空间
- [x] 前缀泄漏检测
- [x] 连续性测试
- [x] 密度分布分析
- [x] 阈值不变性验证
- [ ] 结构吸引子可解释性分析
- [ ] Story Encoder 训练
- [ ] Story Map 发布
