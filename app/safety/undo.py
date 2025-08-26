from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import shutil

BASE = Path("logs/undo"); BASE.mkdir(parents=True, exist_ok=True)

def _hash_path(path: str) -> str:
    return hashlib.sha1(Path(path).resolve().as_posix().encode("utf-8")).hexdigest()[:8]

def make_backup(src_path: str) -> str:
    src = Path(src_path); src.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists(): return ""
    ts = int(time.time())
    token = f"{_hash_path(str(src))}_{ts}"
    dest_dir = BASE / token; dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    meta = {"token": token, "src": str(src), "backup": str(dest), "ts": ts}
    (dest_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return token

def restore(token: str) -> str:
    dir_ = BASE / token
    meta = json.loads((dir_ / "meta.json").read_text(encoding="utf-8"))
    backup = Path(meta["backup"])
    target = Path(meta["src"])
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, target)
    return str(target)

