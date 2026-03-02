# Story Manifold Engine 计划（A方案优先）

日期：2026-03-02
负责人：Nason + Max
状态：进行中（生成阶段）

## 0. 目标与约束

### 目标
在当前 10k 骨架数据基础上，先落地 **A 方案（检索 + LLM 解码）**，构建一个可用、可控、可迭代的结构生成闭环。

### 关键约束
- 当前要求：**生成完成后先不训练**，先做清洗策略讨论与落地。
- 当前数据 schema 已更新（`beats[].name/desc`、`archetype` 为字符串等），旧清洗/训练脚本存在 schema 偏差，需先修正。

---

## 1. 总体路线图（A方案）

## Phase 0：生成完成与冻结（进行中）
- [ ] 跑满 `raw_skeletons` 到 10k
- [ ] 生成完成后冻结快照（只读副本）
- [ ] 停在清洗前，不触发训练

产出：
- `data/raw_skeletons/` 10k+ 可用样本
- 快照与统计报告（数量、字段完整率、重复率）

## Phase 1：数据清洗 v2（优先）
- [ ] 修正清洗器到新 schema
- [ ] 去重（标题/摘要/beat 模板）
- [ ] 质量打分与阈值筛选
- [ ] 产出 cleaned 数据与清洗报告

产出：
- `data/cleaned_skeletons/skeletons_v2.json`
- `reports/cleaning_report_v2.md`

## Phase 2：检索层
- [ ] 文本化策略（用于 embedding）
- [ ] 构建 embedding 索引（FAISS/HNSW）
- [ ] 条件过滤（archetype/ending/stakes/style_tags）

产出：
- 检索服务与评估脚本

## Phase 3：LLM 解码层
- [ ] 结构化 prompt 与 JSON schema 约束
- [ ] 失败重试与自动修复
- [ ] 采样参数模板（稳健/探索）

产出：
- `POST /generate_skeleton`（内部 API）

## Phase 4：评估与上线
- [ ] 指标与评测集
- [ ] 人工抽检流程
- [ ] 版本发布

核心指标：
- Schema 通过率
- 标题重复率
- 近邻新颖度
- 人工可读性/张力评分

---

## 2. Phase 1 细化（清洗 v2）

## 2.1 输入输出与兼容

### 输入
`data/raw_skeletons/sk_*.json`

### 输出
- 主输出：`data/cleaned_skeletons/skeletons_v2.json`
- 审计输出：
  - `data/cleaned_skeletons/rejects_v2.jsonl`
  - `reports/cleaning_report_v2.md`

### schema 规范（清洗后）
保留字段：
- `id`
- `archetype` (str)
- `title` (str)
- `logline` (str)
- `style_tags` (list[str])
- `ending` (enum)
- `stakes` (str)
- `actors` (list[str])
- `beats` (list[{id,name,desc}])
- `tension_curve` (list[float])
- `themes` (list[str])

---

## 2.2 清洗规则（v2）

### A. 硬性校验（不通过直接 reject）
1. JSON 可解析
2. 必填字段存在且类型正确
3. `beats` 长度 6-10（目标 9）
4. 每个 beat 必须有 `name` 与 `desc`
5. `tension_curve` 长度与 beats 对齐（或可重建）
6. `ending` 必须在 `{tragedy,triumph,bittersweet,open,pyrrhic}`

### B. 规范化（通过后清洗）
1. 文本统一（空白、全半角、异常符号）
2. 标题、logline 去首尾噪声
3. actors 白名单映射（超集裁剪）
4. themes/style_tags 去重与标准化

### C. 去重策略（分层）
1. **精确重复**：
   - 完全相同 `title + logline + beats签名` → 去重
2. **高相似重复**：
   - logline 近似（字符级/Jaccard/编辑距）超过阈值 → 保留质量分更高者
3. **标题高频压制**：
   - 高频标题（如 >N）不必全删，但触发“改写候选”或降权
4. **模板句检测**：
   - 若 beats 中模板短语密度过高，降分或剔除

### D. 质量评分（0-100）
建议权重：
- 结构完整度 30
- 语言信息密度 25
- 新颖度（相对近邻）25
- 模板化惩罚 20

默认阈值（首版）：
- `score >= 60` 保留
- `< 60` 进入 rejects

---

## 2.3 质检与验收

每次清洗后输出以下指标：
1. 保留率（keep/total）
2. 标题重复率（前后对比）
3. logline 近重复率（前后对比）
4. archetype 分布漂移（避免偏科）
5. 人工抽样 50 条结果（A/B 对照）

验收门槛（首版建议）：
- Schema 通过率 >= 99%
- 标题重复率下降 >= 40%
- archetype 分布偏差可控（最大类/最小类 <= 1.8）

---

## 3. GitHub 同步策略（强制执行）

当出现以下“较大变化”时，必须同步到 GitHub：
1. 新增/修改计划文档（本次）
2. 清洗规则或阈值变更
3. 新增数据处理脚本
4. API 行为变化

执行规范：
- 每次大变更单独 commit，commit message 清晰
- push 到 `origin`（必要时开 PR）
- 在文档中记录变更时间与影响范围

---

## 4. 下一步（立即执行）

1. 继续跑满 10k（已启用 watchdog）
2. 完成后冻结 raw 快照
3. 按本计划实现 Phase 1 清洗器 v2（先 dry-run 报告，再落地）


---

## 5. 方案1（Beat向量 + Tension加权池化）预实验记录

时间：2026-03-02 13:2x CST  
脚本：`scripts/benchmark_scheme1.py`  
采样：300 条 skeleton（共 2698 beats）

结果：
- 模型加载：6.32s
- Beat 编码：1.70s
- 编码吞吐：1583.1 beats/s
- 估算 10k 样本（按 8.99 beats/条）编码时间：56.8s（约 0.9 分钟，不含训练）

结论：
- 方案1在当前机器上成本很低，可作为下一轮训练默认输入表达方式。
- 下一步：在 clean_v2 完成后，执行 1k 样本小规模训练计时，再决定全量训练参数。

---

## 6. 讨论结论补充（2026-03-02）

以下为本轮讨论确认要纳入路线图的方向。

### 6.1 表达与训练侧

1. **下一轮训练采用方案1（已确认）**
   - Beat 级向量化（每个 beat 单独编码）
   - 使用 `tension_curve` 做加权池化形成 story 向量
   - 先小样本计时，再扩大到训练集

2. **时间/顺序作为显式维度**
   - 在 beat 表达中加入位置特征（pos/t）
   - 从“单点表示”升级为“叙事轨迹表示”

3. **训练后反推类型体系（taxonomy v2）**
   - 使用 encoder 向量 + 聚类（HDBSCAN/层次聚类）
   - 输出旧类型到新簇映射，作为后续生成条件体系基础

4. **语义轴发现与验证**
   - 线性探针 + PCA/ICA 找候选方向
   - 通过沿轴插值并解码验证可解释性

### 6.2 生成与解码侧

5. **A方案优先：检索 + LLM 解码**
   - 先保证可用性和可控性
   - 后续再评估是否投入 latent diffusion（B方案）

6. **分形化 beat 扩展（中长期）**
   - macro beats -> micro beats 的递归展开
   - 加一致性约束（不违背上层目标/结果）与预算约束（长度/张力）

### 6.3 质量优化与反馈学习

7. **清洗重点**
   - 标题重复控制（高频压制 + 改写候选）
   - 模板句密度惩罚

8. **Teacher 打分反馈回路（RLAIF）**
   - teacher 模型多维打分：结构/新颖度/张力/可拍性/模板惩罚
   - 第一阶段先做“打分+重排”，再评估 DPO/IPO/ORPO 微调
   - 暂不优先 PPO（成本与稳定性风险较高）

### 6.4 执行优先级（更新）

- **P0**：clean_v2 + 方案1输入落地 + 1k样本训练计时 + taxonomy反推demo
- **P1**：时间维建模 + 语义轴验证 + 解码自检回路
- **P2**：分形扩展 + teacher偏好学习微调


---

## 7. EMNLP 2024 Story Embeddings 论文对齐建议（已讨论确认）

参考论文：Story Embeddings — Narrative-Focused Representations of Fictional Stories（EMNLP 2024 main 339）
参考仓库：`uhh-lt/story-emb`

### 7.1 可直接迁移的方法

1. **目标保持 narrative similarity**
   - 训练目标聚焦“发生了什么”，弱化表面措辞、命名与风格差异。

2. **对比学习 + in-batch negatives**
   - 沿用对比学习框架，利用 batch 内自然负样本提升区分度。

3. **实体去敏增强（pseudonymization）**
   - 对文本中的实体名做一致替换（如主角A/反派B），作为训练增强视图。
   - 原始文本保留，不做覆盖。

4. **统一 query prefix**
   - 训练与检索阶段统一输入前缀模板，减少训练/推理分布偏差。

5. **检索指标作为主 KPI**
   - 保持 Recall@k / MRR，并补充 MAP / nDCG 作为标准化评估。

### 7.2 数据策略（训练 vs 验证）

1. **主训练集**：`skeletons_v2_main`
2. **鲁棒样本混入**：`skeletons_v2_secondary`（低权重）
3. **外部验证集（优先用于评估，不直接并入主训练）**：
   - Retellings（优先）
   - Movie Remake（次优先）

### 7.3 执行顺序（更新）

1. 跑满 10k 生成
2. 维持 clean v2 分层产物
3. 训练配置：方案1 + 时间维 + 去敏增强视图
4. 小规模正式训练（1k~2k）
5. secondary + external eval（retellings/remake）出 benchmark
6. 再决策全量训练

### 7.4 风险控制

- 不提前将外部数据并入主训练，避免分布漂移。
- 去敏增强必须保证替换一致性，避免噪声。
- 检索指标提升需配套可解释分析（聚类与语义轴）共同验证。


---

## 8. 新增：Known Works 零语料直抽 Pilot（100）

目标：不保存原文、不过外部语料，直接让大模型基于其已知作品知识抽取骨架。

实现：
- 脚本：`scripts/generate_known_works_pilot.py`
- 输出目录：`data/raw_skeletons_known/pilot_100/`
- 过程：
  1) 先让模型生成平衡作品清单（国别/时代/风格）`works_list.json`
  2) 对每部作品生成骨架 JSON（9 beats + tension + confidence）

注意：
- 仅保存结构化骨架与元信息，不保存作品原文。
- 后续将对结果跑 clean_v2 分层与一致性校验。

---

## 9. Anchor 计划（高质量骨架先行）

目标：在大规模扩充前，先构建高质量“叙事锚点”数据，用于校准潜空间品味与结构边界。

### 9.1 分阶段目标

- **Phase A（立即）**：100 anchors（高质量人工/LLM复核）
- **Phase B（通过后）**：500 anchors（覆盖核心题材与结局类型）
- **Phase C（联动10k）**：用 anchors 做重加权/蒸馏校准

### 9.2 Anchor 数据标准

每条 anchor 必须满足：
1. schema 完整（含 9 beats + tension_curve + ending + stakes）
2. 结构逻辑通过（因果、冲突升级、收束一致）
3. 模板化低（重复句式受限）
4. 题材与结局覆盖均衡

### 9.3 训练联动策略

1. 对比学习主干继续使用 main 数据集
2. anchors 在训练中提高采样权重（例如 2x-4x）
3. 增加辅助头：ending/archetype 预测
4. 评估时单独报告 anchor 子集检索指标

### 9.4 与外部建议的落地映射

- Dramatic Arc Vector -> tension_curve 数值标准化
- 多任务 embedding -> 对比学习 + 分类辅助头
- Mix consistency -> 线性插值后 LLM 结构一致性检查
- Graph 化 -> 中长期 Narrative Graph 方向，不阻塞当前里程碑

### 9.5 执行顺序（更新）

1. 完成当前 10k 生成 + pilot 验证
2. 启动 100 anchors 构建与复核
3. 跑小规模训练（含时间维 + anchors重权）
4. 评估通过后扩到 500 anchors
5. 再进入全量训练与 taxonomy v2 反推


---

## 10. 外部建议消化（结构滤镜 / 语义轴 / 一致性评估）

本节整理对“层次化叙事生成、叙事图谱、潜空间漫游、自动评估”建议的落地结论。

### 10.1 采纳项（优先）

1. **Plan → Sketch → Story 分层**
   - 当前项目定位在 Sketch（Skeleton）层，继续强化结构表达与可控性。

2. **Self-Consistency Score（逻辑一致性）**
   - 新增自动评估：检查因果链闭环、冲突升级连续性、结局与前文一致性。
   - 用于 clean/重排阶段与 mix 结果门控。

3. **语义方向向量（Directional Vectors）**
   - 在潜空间中显式构建“悲剧轴”“节奏轴”等方向。
   - 支持对骨架做可控偏移与插值实验。

4. **可视化升级到 Projector**
   - 除静态图外，增加可交互投影以观察样本聚类与 mix 轨迹。

### 10.2 谨慎项（中期）

1. **Graph Merging / GraphRAG**
   - 价值高但工程复杂；先做轻量角色关系矩阵，再决定是否升级为图管线。

2. **外部剧情站点抓取作为主数据**
   - 当前策略不保存原文；外部数据优先作为评估/对照，不直接替换主训练数据。

### 10.3 执行顺序（补充）

- **P0**：Consistency Score + 语义轴探测 + Projector可视化
- **P1**：角色关系拓扑（轻量）
- **P2**：GraphRAG/子图融合

### 10.4 结构滤镜实验（新增）

新增“结构滤镜（Structure Filter）”实验：
- 从两类代表作品计算差分向量 `Δ = V_A - V_B`
- 将 `Δ` 施加到第三类骨架并解码
- 用一致性评分与人工抽检验证“语义偏移是否成立”

---

## 11. 新增：自动生成骨架 vs 名著骨架潜空间对齐计划（2026-03-02 19:41）

结论：**两者潜空间可能不一致，且该风险是常态而非例外**。因此采用“渐进对齐”，不做暴力全量混合。

### 11.1 风险定义（domain mismatch）

可能表现为：
1. 语义轴偏移（同标签在两域中方向不一致）
2. 密度结构不一致（名著分布更稠密/更长尾）
3. 边界样本缺失（自动生成未覆盖稀有结构）

### 11.2 执行原则（固定）

1. 名著数据先作为 external anchor 验证集，不直接并入主训练分布。
2. 对齐训练优先于混训扩量。
3. 混训比例从 **5%** 起步，阶段上限 **10~15%**。
4. 未达标不接入 A 方案链路。

### 11.3 四项必测指标（每轮训练后）

1. **Cross-domain 检索差值**：known→main 与 secondary→main 的 Recall/MRR 对比
2. **分布距离**：MMD / Fréchet（embedding 空间）
3. **聚类来源纯度**：HDBSCAN 后是否按“数据来源域”分裂
4. **线性探针迁移**：在自动生成域训练的语义轴，迁移到名著域的性能掉幅

### 11.4 对齐训练建议（实施顺序）

1. 以 known works 构建 anchor 对比学习批次（正样本近邻、负样本远邻）
2. anchor 提高采样权重（2x~4x）
3. 小比例注入（5%）并评估四项指标
4. 指标稳定改善后再逐步提升到 10~15%

### 11.5 上线闸门（新增）

仅当以下条件同时满足时，允许接入生成链路：
- known→main 检索指标达到或超过当前基线趋势
- 分布距离下降（连续两轮）
- 聚类来源域分裂显著缓解
- 语义轴迁移掉幅进入可接受区间

---

## 12. 执行决策（2026-03-02 20:16）

基于第 1 步检索评估与第 2 步 HDBSCAN 映射结果，确认执行：

1. **先回滚 old 模型作为主链路基线**：`encoder/story-encoder-zh-v2-time`
2. 对 `story-encoder-zh-v2-time-10k` 开展一轮**对齐微调**：
   - external anchor 对比学习（known works）
   - 小比例注入（5% 起步，10~15% 上限）
3. 完成微调后按统一口径复测（检索 + HDBSCAN + 语义轴）
4. **仅在达标后**替换上线

### 12.1 当前状态标记
- 主链路基线：`story-encoder-zh-v2-time`（生效）
- 10k 模型状态：`候选/待对齐微调`

## 13. 对齐微调阶段结果更新（2026-03-02 21:34）

### 13.1 检索复测结论
- `align_v1`（`story-encoder-zh-v2-time-10k-align-v1`）相对 old/10k 基线均显著提升。
- `align_v2` 相对 `align_v1` 全面回退：
  - R@1: 0.671 → 0.645
  - R@5: 0.872 → 0.822
  - R@10: 0.920 → 0.890
  - MRR: 0.760 → 0.729
  - MAP@10: 0.649 → 0.623
  - nDCG@10: 0.432 → 0.382

### 13.2 执行决策
1. 停止继续叠代 `align_v3+`（避免退化）。
2. 当前最优候选固定为：`story-encoder-zh-v2-time-10k-align-v1`。
3. 后续微调仅在有新信号（known works 数据修复后）再恢复。

### 13.3 并行风险（未解决）
- `known_works_1k` 仍为“进程存活但不产出（0/1000）”，日志停留 `JSONDecodeError`，需优先修复生成链路可用性后再引入新 anchor 数据。

## 14. 新增实验（2026-03-02 22:10）

### 14.1 Intrinsic Dimension（align_v1）
- PCA 方差维度：`dim@90%=190`, `dim@95%=296`
- TwoNN 估计：`ID≈7.71`

解读：空间呈“局部低维 + 全局高维”形态，支持叙事自由度可压缩的假设，但不等于全局 10~20 维可完整表达。

### 14.2 Synthetic vs Real Cluster（UMAP）
- synthetic(main)=7260, real(pilot100)=100
- `cross_domain_nn_ratio=0.0042`
- `island_hint=true`

解读：synthetic 与 real 在当前 embedding 空间仍明显分岛，domain mismatch 仍显著，需继续 anchor 对齐与质量修复。

### 14.3 分布距离（新增）
- `MMD^2 (RBF, subsample)=0.1059`
- `Fréchet distance=1.0745`

解读：与 UMAP 分岛结论一致，synthetic / real 仍存在可测分布间隔；后续需继续依赖 anchor 对齐，而非直接混训替换。

