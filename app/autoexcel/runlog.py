import json, time
from pathlib import Path

def log_event(kind: str, payload: dict, dir_="logs/runlogs"):
    Path(dir_).mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    path = Path(dir_) / f"{kind}_{ts}.json"
    payload = {"ts": ts, "kind": kind, **payload}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
