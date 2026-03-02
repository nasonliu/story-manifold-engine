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
