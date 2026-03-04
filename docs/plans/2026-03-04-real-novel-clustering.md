# 真实小说聚类分析计划

## Progress

Current skeletons: **122**

Language distribution:
- zh: ~120 (98%)
- en: 2 (2%)

### Quality Issues Found:
| Issue | Count | % |
|-------|-------|---|
| Template tension_curve | 101 | 82.8% |
| Zero chapter_count | 43 | 35.2% |
| Empty turning_points | 30 | 24.6% |
| Empty beats | 16 | 13.1% |
| Wrong tension length | 17 | 13.9% |
| Template beats | 2 | 1.6% |

**Main Problem**: The model outputs template values instead of extracting real structure from text.

Phase:
- Phase 1 (<2000): IN PROGRESS

## Tasks
- [x] scripts/novel_pipeline.py
- [x] scripts/extract_skeleton.py
- [x] scripts/dataset_balance.py
- [x] scripts/run_clustering.py
- [ ] Fix template extraction issue
- [ ] 达到 2000 skeletons
- [ ] 每100条质量验证

## Next Run
1) 修复 prompt 使模型真正提取而非输出模板
2) 继续提取（本地 deepseek-r1:8b）
3) 补充英文/其他语言数据
4) 提交 GitHub
