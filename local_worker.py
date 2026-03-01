#!/usr/bin/env python3
"""
本地 4090D OpenClaw - Gist 任务执行器
放到本地 WSL 的 story-engine/ 目录下运行
用法: python3 local_worker.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

# 把 gist_queue 加到 path（同目录）
sys.path.insert(0, str(Path(__file__).parent))
from gist_queue import read_task, write_task, now_str

POLL_INTERVAL = 30  # 秒，轮询间隔


def run_cmd(cmd: str) -> tuple[int, str]:
    """执行 shell 命令，返回 (returncode, output)"""
    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True,
            timeout=3600,  # 最长1小时
            cwd=str(Path(__file__).parent),
        )
        output = result.stdout + result.stderr
        return result.returncode, output[-8000:]  # 截取最后8000字符
    except subprocess.TimeoutExpired:
        return -1, "超时（>1小时）"
    except Exception as e:
        return -1, str(e)


def main():
    print(f"🤖 本地 Worker 启动，轮询间隔 {POLL_INTERVAL}s")
    print(f"📋 Gist: https://gist.github.com/nasonliu/0e141c269ffe02b16db6e10385aded9e")

    while True:
        try:
            task = read_task()
            status = task.get("status", "")
            task_id = task.get("id", "?")

            if status == "pending":
                cmd = task.get("cmd", "")
                print(f"\n[{now_str()}] 📥 收到任务 {task_id}: {cmd[:60]}")

                # 先 ack
                task["status"] = "running"
                task["ack_at"] = now_str()
                write_task(task)
                print(f"  ✅ 已 ack")

                # 执行
                print(f"  ⚙️  执行中...")
                rc, output = run_cmd(cmd)
                print(f"  完成 (rc={rc})，输出 {len(output)} 字符")

                # 写结果
                task["status"] = "done"
                task["returncode"] = rc
                task["output"] = output
                task["done_at"] = now_str()
                write_task(task)
                print(f"  📤 结果已写回 Gist")

            elif status in ("ready", "done", "running"):
                print(f"[{now_str()}] 💤 {status}，等待...")
            else:
                print(f"[{now_str()}] ❓ 未知状态: {status}")

        except Exception as e:
            print(f"[{now_str()}] ❌ 错误: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
