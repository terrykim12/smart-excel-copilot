# tools/watch_run.py
from __future__ import annotations
import time, json, pathlib, threading, sys
from queue import Queue, Empty

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.io.loader import detect_encoding, load_table
from app.report.template import build_report

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except Exception:
    HAS_WATCHDOG = False

OUTDIR = ROOT / "data" / "report"; OUTDIR.mkdir(parents=True, exist_ok=True)

def _process_file(path: str):
    enc = detect_encoding(path)
    df, _ = load_table(path, encoding=enc.get("encoding"))
    out = OUTDIR / f"auto_{pathlib.Path(path).stem}.xlsx"
    rep = build_report(df, str(out), title=f"자동 보고서 — {pathlib.Path(path).name}", period="Auto", owner="Watcher")
    return {"in": path, "out": str(out), **rep}

def watch_dir(dir_path: str, pattern=(".csv",".xlsx")):
    q: Queue[str] = Queue()

    def worker():
        seen = {}
        while True:
            try:
                p = q.get(timeout=1)
            except Empty:
                continue
            try:
                if pathlib.Path(p).suffix.lower() not in pattern: 
                    continue
                # 같은 파일 연속 이벤트 디바운스 (5초)
                now = time.time()
                if p in seen and now - seen[p] < 5: 
                    continue
                seen[p] = now
                info = _process_file(p)
                print(json.dumps({"event":"processed","info":info}, ensure_ascii=False))
            except Exception as e:
                print(json.dumps({"event":"error","file":p,"error":str(e)}, ensure_ascii=False))

    th = threading.Thread(target=worker, daemon=True); th.start()

    if HAS_WATCHDOG:
        class H(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory: q.put(event.src_path)
            def on_modified(self, event):
                if not event.is_directory: q.put(event.src_path)

        obs = Observer()
        obs.schedule(H(), dir_path, recursive=False)
        obs.start()
        print(json.dumps({"watching":dir_path,"engine":"watchdog"}, ensure_ascii=False))
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            obs.stop(); obs.join()
    else:
        print(json.dumps({"watching":dir_path,"engine":"polling"}, ensure_ascii=False))
        mtimes = {}
        try:
            while True:
                for p in pathlib.Path(dir_path).glob("*"):
                    if p.suffix.lower() in pattern:
                        m = p.stat().st_mtime
                        if p not in mtimes or m > mtimes[p]:
                            mtimes[p] = m
                            q.put(str(p))
                time.sleep(2)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str((ROOT/"data"/"incoming")))
    args = ap.parse_args()
    pathlib.Path(args.dir).mkdir(parents=True, exist_ok=True)
    watch_dir(args.dir)
