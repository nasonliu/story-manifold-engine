import json, subprocess, sys, time, platform, fcntl, os
sys.path.insert(0, "/home/nason/.openclaw/workspace")
from gist_queue import read_all, local_ack, local_write_result, local_heartbeat

LOCK = "/tmp/gist_worker.lock"

def main():
    lf = open(LOCK, "w")
    try:
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        sys.exit(0)

    try:
        local_heartbeat({"hostname": platform.node(), "python": platform.python_version(), "gpu": "RTX 4090D 24GB"})

        state = read_all()
        task = state["task"]
        status = task.get("status", "")

        if status == "pending":
            print(f"[worker] 收到任务 {task.get('id')}: {task.get('cmd','')[:60]}")
            local_ack(task)
            r = subprocess.run(
                task["cmd"], shell=True, capture_output=True, text=True,
                timeout=7200, cwd="/home/nason/.openclaw/workspace"
            )
            out = (r.stdout + r.stderr)[-6000:]
            local_write_result(task, r.returncode, out)
            print(f"[worker] 完成 rc={r.returncode}")
        else:
            print(f"[worker] 状态={status}，心跳已上报")
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)
        lf.close()

if __name__ == "__main__":
    main()
