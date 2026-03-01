import os
#!/usr/bin/env python3
"""
Story Engine Gist 任务队列 - 双向通信协议 v2
支持：云端→本地 下发任务，本地→云端 上报结果 + 心跳

Gist 文件结构：
  task.json     — 当前任务（云端写，本地读执行）
  heartbeat.json — 本地心跳（本地写，云端读确认存活）
  log.json      — 双向操作日志

状态流转：
  idle     → 云端无任务
  pending  → 云端已写任务，等待本地
  ack      → 本地已收到，执行中
  done     → 本地执行完成
  error    → 本地执行失败
  cancel   → 云端取消任务
"""
import json
import urllib.request
from datetime import datetime, timezone

GITHUB_TOKEN = "os.environ.get("GITHUB_TOKEN", "")"
GIST_ID      = "0e141c269ffe02b16db6e10385aded9e"
GIST_API     = f"https://api.github.com/gists/{GIST_ID}"
HEADERS      = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}

def now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _req(method, url, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def _parse_file(gist_data, filename):
    f = gist_data.get("files", {}).get(filename)
    if not f:
        return {}
    try:
        return json.loads(f["content"])
    except Exception:
        return {}

def _update_files(files_dict):
    """批量更新 Gist 多个文件"""
    payload = {"files": {}}
    for name, obj in files_dict.items():
        payload["files"][name] = {"content": json.dumps(obj, ensure_ascii=False, indent=2)}
    _req("PATCH", GIST_API, payload)

def read_all():
    """读取全部文件"""
    d = _req("GET", GIST_API)
    return {
        "task":      _parse_file(d, "task.json"),
        "heartbeat": _parse_file(d, "heartbeat.json"),
        "log":       _parse_file(d, "log.json"),
    }

# ── 云端调用 ────────────────────────────────────────────
def cloud_send_task(task_id, cmd, note=""):
    """云端下发任务"""
    state = read_all()
    task = {
        "id": task_id,
        "status": "pending",
        "cmd": cmd,
        "note": note,
        "sent_at": now_str(),
        "output": "",
        "returncode": None,
    }
    log = state.get("log", {"entries": []})
    log.setdefault("entries", []).append(
        {"ts": now_str(), "side": "cloud", "event": f"sent task {task_id}"}
    )
    _update_files({"task.json": task, "log.json": log})
    return task

def cloud_read_result():
    """云端读取本地执行结果"""
    state = read_all()
    task = state["task"]
    hb   = state.get("heartbeat", {})
    return task, hb

def cloud_confirm_result(task_id):
    """云端确认已读结果，重置为 idle"""
    state = read_all()
    task = state["task"]
    if task.get("id") == task_id and task.get("status") == "done":
        task["status"] = "idle"
        task["cloud_ack_at"] = now_str()
        log = state.get("log", {"entries": []})
        log.setdefault("entries", []).append(
            {"ts": now_str(), "side": "cloud", "event": f"acked result {task_id}"}
        )
        _update_files({"task.json": task, "log.json": log})
        return True
    return False

# ── 本地调用 ────────────────────────────────────────────
def local_ack(task):
    """本地确认收到任务"""
    task["status"] = "ack"
    task["ack_at"] = now_str()
    _update_files({"task.json": task})

def local_write_result(task, returncode, output):
    """本地写回执行结果"""
    task["status"] = "done" if returncode == 0 else "error"
    task["returncode"] = returncode
    task["output"] = output[-6000:]
    task["done_at"] = now_str()
    _update_files({"task.json": task})

def local_heartbeat(info=None):
    """本地心跳上报"""
    hb = {
        "ts": now_str(),
        "status": "alive",
        "info": info or {},
    }
    _update_files({"heartbeat.json": hb})
