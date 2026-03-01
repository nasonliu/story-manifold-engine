# Story Manifold Engine

> 从大模型蒸馏叙事结构，构建故事潜空间。

## 项目目标

不是 AI 写作工具，而是**叙事操作系统**：

- 学习故事结构的低维潜空间（Story Manifold）
- 支持：相似故事检索 / 结构混合 / 新骨架生成
- 为 IP 生产、短剧创作、游戏叙事提供结构引擎

## 架构

```
Teacher LLM（生成骨架）
        ↓
Story Skeleton Dataset（JSON）
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
│   └── embeddings/         # 向量文件
├── generator/
│   ├── clean_skeletons.py  # 清洗 & 去重
│   └── validator.py        # Schema 校验
├── encoder/
│   └── train_encoder.py    # 对比学习训练
├── analysis/
│   └── visualize.py        # UMAP 可视化
├── api/
│   └── server.py           # FastAPI 服务
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 清洗骨架数据

```bash
cd story-engine
python generator/clean_skeletons.py
```

### 3. 训练 Encoder

```bash
python encoder/train_encoder.py
```

> 4090D 约 2–4 小时（10k skeletons）

### 4. 可视化 Story Map

```bash
python analysis/visualize.py
# 打开 data/story_map.html
```

### 5. 启动 API

```bash
cd api
uvicorn server:app --reload --port 8000
```

### API 接口

| 接口 | 说明 |
|------|------|
| `POST /search` | 输入文本，找相似骨架 |
| `POST /mix` | 两个骨架 ID + alpha，混合结构 |
| `GET /skeleton/{id}` | 获取单条骨架 |
| `GET /stats` | 数据集统计 |

## Skeleton Schema

```json
{
  "id": "sk_001",
  "archetype": ["复仇"],
  "beats": [
    {"id": "B1", "event": "主角遭至亲背叛", "actors": ["主角", "叛徒"], "stakes": "生命"},
    ...
  ],
  "twist_count": 2,
  "ending": "pyrrhic",
  "style_tags": ["古装"]
}
```

**ending 类型：**
- `tragedy` 悲剧
- `triumph` 胜利
- `bittersweet` 苦乐参半
- `open` 开放结局
- `pyrrhic` 惨胜

## 路线图

- [x] Skeleton 生成（Teacher LLM）
- [x] 数据清洗 & 校验
- [x] Story Encoder 训练脚本
- [x] UMAP 可视化
- [x] FastAPI 服务
- [ ] 生成 10k+ skeletons
- [ ] 训练完整 Encoder
- [ ] Story Map 发布
- [ ] Narrative Graph 扩展
- [ ] 多模态输出（短剧剧本 / 游戏事件树）
