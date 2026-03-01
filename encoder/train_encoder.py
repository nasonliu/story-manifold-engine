#!/usr/bin/env python3
"""
Story Encoder 训练脚本
基于 sentence-transformers + 对比学习
用法：python train_encoder.py

需要安装：
pip install sentence-transformers torch
"""
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

SKELETONS_FILE = Path("data/cleaned_skeletons/skeletons.json")
MODEL_OUT = Path("encoder/story-encoder-zh")
BASE_MODEL = "BAAI/bge-base-zh-v1.5"  # 中文 base encoder

def skeleton_to_text(sk: dict, mode="full") -> str:
    """把 skeleton 转成文本表示"""
    beats = sk.get("beats", [])
    archetype = "、".join(sk.get("archetype", []))

    if mode == "full":
        events = " → ".join(b["event"] for b in beats)
        return f"【{archetype}】{events}"
    elif mode == "short":
        # 只用关键 beats（首/中/尾）
        key = [beats[0], beats[len(beats)//2], beats[-1]]
        events = " → ".join(b["event"] for b in key)
        return f"[{archetype}] {events}"
    elif mode == "archetype_only":
        return f"故事类型：{archetype}，结局：{sk.get('ending', '')}，反转数：{sk.get('twist_count', 0)}"

def build_training_pairs(skeletons: list) -> list:
    """构建正样本对：同一 skeleton 的不同文本表示"""
    pairs = []
    for sk in skeletons:
        text_full = skeleton_to_text(sk, "full")
        text_short = skeleton_to_text(sk, "short")
        text_meta = skeleton_to_text(sk, "archetype_only")

        # 同一 skeleton 的不同表示 = 正样本对
        pairs.append(InputExample(texts=[text_full, text_short]))
        pairs.append(InputExample(texts=[text_full, text_meta]))
        pairs.append(InputExample(texts=[text_short, text_meta]))

    return pairs

def main():
    print(f"Loading skeletons from {SKELETONS_FILE}...")
    with open(SKELETONS_FILE) as f:
        skeletons = json.load(f)
    print(f"  {len(skeletons)} skeletons loaded")

    print(f"\nLoading base model: {BASE_MODEL}")
    model = SentenceTransformer(BASE_MODEL)

    print("\nBuilding training pairs...")
    pairs = build_training_pairs(skeletons)
    print(f"  {len(pairs)} pairs")

    train_loader = DataLoader(pairs, shuffle=True, batch_size=32)
    loss = losses.MultipleNegativesRankingLoss(model)

    print("\nTraining...")
    model.fit(
        train_objectives=[(train_loader, loss)],
        epochs=5,
        warmup_steps=100,
        show_progress_bar=True,
        output_path=str(MODEL_OUT),
    )

    print(f"\n✅ Model saved → {MODEL_OUT}")

if __name__ == "__main__":
    main()
