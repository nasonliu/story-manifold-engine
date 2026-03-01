#!/usr/bin/env python3
"""
Story Manifold Engine - 一键训练脚本
在 WSL Ubuntu + RTX 4090D 上运行

用法：
  cd ~/story-engine
  python3 run_training.py

会自动：
1. 检查环境
2. 安装依赖
3. 下载 base model
4. 构建训练数据
5. 训练 story encoder
6. 保存模型到 encoder/story-encoder-zh/
"""

import subprocess
import sys
import json
import os
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
SKELETONS_FILE = BASE_DIR / "data" / "cleaned_skeletons" / "skeletons.json"
MODEL_OUT      = BASE_DIR / "encoder" / "story-encoder-zh"
BASE_MODEL     = "BAAI/bge-base-zh-v1.5"
BATCH_SIZE     = 64    # 4090D 24GB 轻松跑，可调大
EPOCHS         = 10
WARMUP_STEPS   = 200

# ── Step 1: 检查依赖 ────────────────────────────────────
def check_and_install():
    print("=" * 60)
    print("Step 1: 检查 & 安装依赖")
    print("=" * 60)

    packages = [
        "torch",
        "sentence-transformers",
        "transformers",
        "tqdm",
    ]

    missing = []
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} 未安装")
            missing.append(pkg)

    if missing:
        print(f"\n  正在安装: {missing}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--quiet", "--upgrade",
        ] + missing)
        print("  安装完成！")

    # 检查 GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"\n  🎮 GPU: {gpu} ({vram:.1f} GB VRAM)")
        else:
            print("\n  ⚠️  未检测到 GPU，将使用 CPU（训练会很慢）")
    except Exception as e:
        print(f"  GPU 检查失败: {e}")


# ── Step 2: 构建训练数据 ────────────────────────────────
def build_training_data():
    print("\n" + "=" * 60)
    print("Step 2: 构建训练数据")
    print("=" * 60)

    if not SKELETONS_FILE.exists():
        print(f"  ❌ 找不到数据文件: {SKELETONS_FILE}")
        sys.exit(1)

    with open(SKELETONS_FILE, encoding="utf-8") as f:
        skeletons = json.load(f)

    print(f"  📂 加载 {len(skeletons)} 个骨架")

    # 按原型分组
    from collections import defaultdict
    by_archetype = defaultdict(list)
    for sk in skeletons:
        by_archetype[sk["archetype"]].append(sk)

    print(f"  📊 {len(by_archetype)} 个原型，每原型平均 {len(skeletons)/len(by_archetype):.0f} 个")

    def sk_to_text(sk, mode="full"):
        """把骨架转成自然语言文本"""
        arch  = sk.get("archetype", "")
        beats = sk.get("beats", [])
        beat_names = " → ".join(b.get("name", "") for b in beats)
        beat_descs = " | ".join(b.get("desc", "")[:40] for b in beats[:3])
        ending = sk.get("ending", "")
        stakes = sk.get("stakes", "")
        themes = "、".join(sk.get("themes", []))
        actors = "、".join(sk.get("actors", []))

        if mode == "beats_full":
            # 完整节拍序列
            return f"【{arch}】{beat_names}。核心矛盾：{stakes}。结局：{ending}。"
        elif mode == "beats_desc":
            # 前三个节拍的描述
            return f"【{arch}】{beat_descs}。主题：{themes}。"
        elif mode == "meta":
            # 元信息
            return f"叙事原型：{arch}。角色：{actors}。利害：{stakes}。结局：{ending}。主题：{themes}。"
        elif mode == "logline":
            # logline
            return f"【{arch}】{sk.get('logline', '')}结局：{ending}。"

    # 构建正例对（同原型不同骨架 = 正例，不同骨架不同表示也是正例）
    from sentence_transformers import InputExample

    pairs = []

    # 策略1：同一骨架的不同文本表示（跨模态）
    for sk in skeletons:
        texts = [
            sk_to_text(sk, "beats_full"),
            sk_to_text(sk, "beats_desc"),
            sk_to_text(sk, "meta"),
            sk_to_text(sk, "logline"),
        ]
        # 两两配对
        for i in range(len(texts)):
            for j in range(i+1, len(texts)):
                pairs.append(InputExample(texts=[texts[i], texts[j]]))

    # 策略2：同原型不同骨架（跨实例）——这是核心训练信号
    for arch, sks in by_archetype.items():
        if len(sks) < 2:
            continue
        import random
        random.shuffle(sks)
        for i in range(len(sks) - 1):
            a = sk_to_text(sks[i],   "beats_full")
            b = sk_to_text(sks[i+1], "beats_full")
            pairs.append(InputExample(texts=[a, b]))
            # 也加 meta 对
            a2 = sk_to_text(sks[i],   "meta")
            b2 = sk_to_text(sks[i+1], "meta")
            pairs.append(InputExample(texts=[a2, b2]))

    print(f"  🔗 训练对数量: {len(pairs)}")
    return pairs


# ── Step 3: 训练 ────────────────────────────────────────
def train(pairs):
    print("\n" + "=" * 60)
    print("Step 3: 训练 Story Encoder")
    print("=" * 60)

    from sentence_transformers import SentenceTransformer, losses
    from torch.utils.data import DataLoader
    import torch

    print(f"  📥 加载 base model: {BASE_MODEL}")
    model = SentenceTransformer(BASE_MODEL)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  💻 训练设备: {device}")
    if device == "cuda":
        print(f"  🎮 {torch.cuda.get_device_name(0)}")

    train_loader = DataLoader(pairs, shuffle=True, batch_size=BATCH_SIZE)
    loss_fn = losses.MultipleNegativesRankingLoss(model)

    total_steps = len(train_loader) * EPOCHS
    print(f"  📊 总步数: {total_steps} ({len(train_loader)} steps × {EPOCHS} epochs)")
    print(f"  🔄 Batch size: {BATCH_SIZE}")
    print(f"  🔥 开始训练...\n")

    MODEL_OUT.mkdir(parents=True, exist_ok=True)

    model.fit(
        train_objectives=[(train_loader, loss_fn)],
        epochs=EPOCHS,
        warmup_steps=WARMUP_STEPS,
        show_progress_bar=True,
        output_path=str(MODEL_OUT),
        checkpoint_path=str(MODEL_OUT / "checkpoints"),
        checkpoint_save_steps=len(train_loader) * 2,  # 每2epoch存一次
    )

    return model


# ── Step 4: 验证 ────────────────────────────────────────
def validate(model):
    print("\n" + "=" * 60)
    print("Step 4: 快速验证")
    print("=" * 60)

    import torch
    import numpy as np

    test_cases = [
        ("【复仇】隐忍蛰伏 → 重返漩涡 → 最终清算。核心矛盾：灵魂。结局：pyrrhic。",
         "【复仇】归来者的蛰伏 → 悄无声息的渗透 → 代价的揭示。核心矛盾：灵魂。结局：tragedy。"),  # 应该相近

        ("【复仇】隐忍蛰伏 → 重返漩涡 → 最终清算。核心矛盾：灵魂。结局：pyrrhic。",
         "【禁忌之恋】宿命相遇 → 秘密盟誓 → 炽热陨落。核心矛盾：爱情。结局：tragedy。"),  # 应该较远

        ("【英雄成长】平凡世界 → 命运召唤 → 终极试炼。核心矛盾：信念。结局：triumph。",
         "【牺牲】平静的裂痕 → 仪式性的剥离 → 徒劳的静默。核心矛盾：生命。结局：tragedy。"),  # 应该很远
    ]

    print("  相似度测试（越接近1越相似，越接近0越不同）：\n")
    for a, b in test_cases:
        emb = model.encode([a, b], normalize_embeddings=True, convert_to_tensor=True)
        sim = torch.nn.functional.cosine_similarity(emb[0], emb[1], dim=0).item()
        arch_a = a[1:a.index("】")]
        arch_b = b[1:b.index("】")]
        label = "同原型" if arch_a == arch_b else "跨原型"
        print(f"  [{label}] {arch_a} vs {arch_b}: {sim:.4f}")

    print(f"\n  ✅ 模型保存至: {MODEL_OUT}")
    print(f"  📦 模型大小: {sum(f.stat().st_size for f in MODEL_OUT.rglob('*') if f.is_file()) / 1024**2:.1f} MB")


# ── Main ────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Story Manifold Engine - Encoder Training")
    print(f"📂 工作目录: {BASE_DIR}\n")

    check_and_install()
    pairs = build_training_data()
    model = train(pairs)
    validate(model)

    print("\n" + "=" * 60)
    print("🎉 全部完成！")
    print(f"   模型路径: {MODEL_OUT}")
    print(f"   下一步: 用 analysis/visualize.py 生成 Story Map")
    print("=" * 60)
