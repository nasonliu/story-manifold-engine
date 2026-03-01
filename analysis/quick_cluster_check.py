#!/usr/bin/env python3
"""
用 TF-IDF + 余弦相似度验证骨架聚类假设
不需要任何 ML 库，纯标准库
"""
import json, math, random
from collections import defaultdict, Counter

with open('data/cleaned_skeletons/skeletons.json') as f:
    data = json.load(f)

def sk_text(sk):
    beats = ' '.join(b['name'] for b in sk.get('beats', []))
    themes = ' '.join(sk.get('themes', []))
    return f"{sk['archetype']} {sk['ending']} {sk['stakes']} {beats} {themes}"

texts = [sk_text(sk) for sk in data]

# 字符 bigram TF-IDF
def bigrams(text):
    chars = list(text.replace(' ', ''))
    return [chars[i]+chars[i+1] for i in range(len(chars)-1)]

all_bgs = [bigrams(t) for t in texts]
doc_freq = Counter()
for bg in all_bgs:
    for tok in set(bg):
        doc_freq[tok] += 1
N = len(texts)
idf = {k: math.log(N / v) for k, v in doc_freq.items()}

def tfidf(text):
    bg = bigrams(text)
    tf = Counter(bg)
    total = sum(tf.values())
    return {k: (v / total) * idf.get(k, 0) for k, v in tf.items()}

def cosine(a, b):
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))
    na = math.sqrt(sum(v**2 for v in a.values()))
    nb = math.sqrt(sum(v**2 for v in b.values()))
    return dot / (na * nb) if na * nb > 0 else 0

vecs = [tfidf(t) for t in texts]

# 按原型分组
by_arch = defaultdict(list)
for i, sk in enumerate(data):
    by_arch[sk['archetype']].append((i, vecs[i]))

random.seed(42)
print("=== 组内 vs 组间相似度 ===\n")
print(f"{'原型':<12}  组内avg  组间avg  分离度")
print("-" * 45)

intra_all, inter_all = [], []
all_vecs = list(vecs)

for arch in sorted(by_arch.keys()):
    group = by_arch[arch]
    others = [(i, v) for a, g in by_arch.items() if a != arch for i, v in g]

    pairs_in = [(group[i][1], group[j][1])
                for i in range(len(group)) for j in range(i+1, len(group))]
    sample_in = random.sample(pairs_in, min(40, len(pairs_in)))
    intra = sum(cosine(a, b) for a, b in sample_in) / len(sample_in)

    sample_out = [(random.choice(group)[1], random.choice(others)[1]) for _ in range(40)]
    inter = sum(cosine(a, b) for a, b in sample_out) / len(sample_out)

    sep = (intra - inter) / (inter + 1e-9)
    intra_all.append(intra)
    inter_all.append(inter)
    star = "★" if sep > 0.3 else ("▲" if sep > 0.1 else "·")
    print(f"{arch:<12}  {intra:.4f}   {inter:.4f}   +{sep:.2f}  {star}")

avg_in  = sum(intra_all) / len(intra_all)
avg_out = sum(inter_all) / len(inter_all)
overall = (avg_in - avg_out) / avg_out

print()
print(f"平均组内相似度: {avg_in:.4f}")
print(f"平均组间相似度: {avg_out:.4f}")
print(f"整体分离度:    +{overall:.1%}")
print()

# 最容易混淆的原型对
print("=== 最相似的原型对（可能难以区分）===")
arch_centroids = {}
for arch, group in by_arch.items():
    vecs_g = [v for _, v in group]
    all_keys = set().union(*vecs_g)
    centroid = {k: sum(v.get(k, 0) for v in vecs_g) / len(vecs_g) for k in all_keys}
    arch_centroids[arch] = centroid

arch_list = sorted(arch_centroids.keys())
pairs = []
for i in range(len(arch_list)):
    for j in range(i+1, len(arch_list)):
        a, b = arch_list[i], arch_list[j]
        sim = cosine(arch_centroids[a], arch_centroids[b])
        pairs.append((sim, a, b))

pairs.sort(reverse=True)
print("最相似（难区分）:")
for sim, a, b in pairs[:5]:
    print(f"  {a} <-> {b}: {sim:.4f}")
print("最不同（好区分）:")
for sim, a, b in pairs[-5:]:
    print(f"  {a} <-> {b}: {sim:.4f}")
