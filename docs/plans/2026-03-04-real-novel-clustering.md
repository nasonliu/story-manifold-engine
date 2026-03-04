# 真实小说聚类分析计划

## Progress

Current skeletons: 67

Language distribution:
- zh: 63 (94.0%)
- en: 1 (1.5%)
- unknown/malformed: 3 (4.5%)

Cluster metrics:
- Cluster count proxy: 23
- Silhouette: pending
- Davies-Bouldin: pending

Phase:
- Phase 1 (<2000): IN PROGRESS

## Tasks
- [x] scripts/novel_pipeline.py
- [x] scripts/extract_skeleton.py
- [x] scripts/dataset_balance.py
- [x] scripts/run_clustering.py
- [ ] 达到 2000 skeletons
- [ ] 每100条质量验证
- [ ] 每500条聚类报告
- [ ] 维持比例约束（zh<=35/en40/classic15/other10）

## Next Run
1) 继续本地 deepseek-r1:8b 提取
2) 补充英文/经典/其他语言原始数据
3) 运行 balance + clustering
4) 更新 README / 报告 / 计划
5) 提交 GitHub
