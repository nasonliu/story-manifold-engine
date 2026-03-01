#!/bin/bash
# Story Manifold Engine - 本地 4090D 快速启动
# 用法: bash setup.sh

set -e
echo "=== Story Manifold Engine Setup ==="

# 1. 安装依赖
echo "[1/3] 安装 Python 依赖..."
pip3 install torch sentence-transformers --break-system-packages -q
echo "✅ 依赖安装完成"

# 2. 验证 GPU
echo "[2/3] 检查 GPU..."
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    print(f'   VRAM: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f} GB')
else:
    print('⚠️  未检测到 GPU，将使用 CPU')
"

# 3. 开始训练
echo "[3/3] 开始训练..."
python3 run_training.py

echo "=== 完成！模型保存在 encoder/story-encoder-zh/ ==="
