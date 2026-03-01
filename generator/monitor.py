#!/usr/bin/env python3
"""
监控5个worker进程，全部完成后合并文件并发飞书通知
"""
import time
import subprocess
import os
from pathlib import Path

PIDS_TO_WATCH = [16613, 16619, 16666, 16702, 16703]
TARGET = 500
RAW_DIR = Path("/workspace/story-engine/data/raw_skeletons")

def count_files():
    return len(list(RAW_DIR.glob("sk_*.json")))

def all_done():
    for pid in PIDS_TO_WATCH:
        try:
            os.kill(pid, 0)
            return False  # 还活着
        except ProcessLookupError:
            pass
    return True

print("🔍 开始监控...")
start = time.time()

while True:
    n = count_files()
    elapsed = time.time() - start
    remaining = max(0, TARGET - n)
    rate = (n - 25) / elapsed if elapsed > 0 else 0
    eta = remaining / rate if rate > 0 else 0
    print(f"[{elapsed/60:.0f}min] {n}/{TARGET} 个 | 速率 {rate*60:.0f}/min | 预计还需 {eta/60:.0f}min")

    if all_done():
        print("✅ 所有 worker 进程已结束！")
        break

    time.sleep(60)

# 合并
print("\n📦 合并骨架文件...")
result = subprocess.run(
    ["python3", "generator/merge_skeletons.py"],
    cwd="/workspace/story-engine",
    capture_output=True, text=True
)
print(result.stdout)

final_count = count_files()
failed = TARGET - final_count

# 写结果摘要到文件，供通知脚本读取
summary = f"共 {final_count} 个骨架，失败 {failed} 个，耗时 {(time.time()-start)/60:.0f} 分钟"
Path("/tmp/story_engine_done.txt").write_text(summary)
print(f"\n📝 {summary}")
