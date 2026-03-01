import os
import json, urllib.request, subprocess, platform
from datetime import datetime, timezone

GITHUB_TOKEN = "os.environ.get("GITHUB_TOKEN", "")"
GIST_ID      = "0e141c269ffe02b16db6e10385aded9e"
GIST_API     = f"https://api.github.com/gists/{GIST_ID}"
HEADERS      = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json", "Content-Type": "application/json"}

def now_str(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _req(method, url, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp: return json.loads(resp.read())

def _parse(gist, name):
    f = gist.get("files", {}).get(name)
    return json.loads(f["content"]) if f else {}

def _patch(files):
    _req("PATCH", GIST_API, {"files": {k: {"content": json.dumps(v, ensure_ascii=False, indent=2)} for k, v in files.items()}})

def read_all():
    d = _req("GET", GIST_API)
    return {"task": _parse(d, "task.json"), "heartbeat": _parse(d, "heartbeat.json"), "log": _parse(d, "log.json")}

def local_ack(task):
    task["status"] = "ack"; task["ack_at"] = now_str()
    _patch({"task.json": task})

def local_write_result(task, rc, output):
    task["status"] = "done" if rc == 0 else "error"
    task["returncode"] = rc
    task["output"] = output[-6000:]
    task["done_at"] = now_str()
    _patch({"task.json": task})

def local_heartbeat(info=None):
    _patch({"heartbeat.json": {"ts": now_str(), "status": "alive", "info": info or {}}})
