# 真实小说聚类分析计划

## Progress

Current skeletons: **326** (正在提取中)

Language distribution:
- zh: ~155 (96%)
- en: 6 (4%)

### Quality Issues Found:
| Issue | Count | % |
|-------|-------|---|
| Template tension_curve | ~104 | 82.8% |
| Zero chapter_count | ~44 | 35.2% |
| Empty turning_points | ~31 | 24.6% |
| Empty beats | ~16 | 13.1% |
| Wrong tension length | ~18 | 13.9% |

**Main Problem**: The model outputs template values instead of extracting real structure from text.

Phase:
- Phase 1 (<2000): IN PROGRESS

## Tasks
- [x] scripts/novel_pipeline.py
- [x] scripts/extract_skeleton.py
- [x] scripts/dataset_balance.py
- [x] scripts/run_clustering.py
- [ ] 修复 prompt 使模型真正提取
- [ ] 达到 2000 skeletons
- [ ] 每100条质量验证

## 后台任务状态
- PID 27967: novel_pipeline.py --batch 100 (运行中)
- PID 28080: novel_pipeline.py --batch 50 (运行中)
- Ollama: 运行中

## Next Run
1) 等待提取完成
2) 提交 GitHub
3) 分析质量改进方案
