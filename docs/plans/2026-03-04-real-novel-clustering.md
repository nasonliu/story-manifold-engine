# 真实小说聚类分析计划

**状态**: 🔴 进行中  
**更新**: 2026-03-04 08:50

---

## Progress

### Current Skeletons: 3

### Language Distribution
- Chinese (zh): 3
- English (en): 0
- Other: 0

### Target Distribution (Phase 1: 2000)
- Chinese web novels: 700 (35%)
- English: 800 (40%)
- Classic literature: 300 (15%)
- Other languages: 200 (10%)

---

## Pipeline

### Using Local Model
- Model: DeepSeek R1 8B via Ollama
- Endpoint: http://localhost:11434

### Skeleton Schema
```json
{
  "title": "",
  "author": "",
  "language": "",
  "genre": "",
  "structure": {
    "beats": [],
    "turning_points": [],
    "climax_position": 0.6,
    "tension_curve": []
  },
  "summary": "",
  "chapter_count": 0
}
```

---

## Data Files

- Raw: data/real_novels_raw/
- Skeletons: data/real_novels_skeletons/

---

## Scripts

- scripts/novel_pipeline.py - Main extraction pipeline

---

## Phase 1 Target

| Language | Target | Current |
|----------|--------|---------|
| Chinese | 700 | 3 |
| English | 800 | 0 |
| Classic | 300 | 0 |
| Other | 200 | 0 |
| **Total** | **2000** | **3** |

---

## Running

```bash
python scripts/novel_pipeline.py --batch 10
```
