import subprocess, sys, json, time, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
GS = ROOT / "data" / "goldensets"
LOGDIR = ROOT / "logs" / "golden_runs"
LOGDIR.mkdir(parents=True, exist_ok=True)

FILES = sorted([p for p in GS.iterdir() if p.is_file() and p.suffix.lower() in (".csv",".xlsx")])

def run(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, text=True, capture_output=True)
    dt = time.time() - t0
    return p.returncode, round(dt,3), p.stdout, p.stderr

def main():
    results = []
    for f in FILES:
        rc1, t1, so1, se1 = run([sys.executable, "-m", "app.cli", "profile", "--path", str(f)])
        rc2, t2, so2, se2 = run([sys.executable, "-m", "app.cli", "preprocess", "--path", str(f), "--dry-run"])
        rc3, t3, so3, se3 = run([sys.executable, "-m", "app.cli", "preprocess", "--path", str(f), "--apply"])
        rc = max(rc1, rc2, rc3)
        sec = t1 + t2 + t3
        status = "OK" if rc == 0 else "ERROR"
        print(f"[golden] {status} {f.name}: {sec}s")
        if rc != 0:
            print(se1 or se2 or se3)
        results.append({"file": f.name, "seconds": sec, "rc": rc})
    out = {"results": results, "ts": int(time.time())}
    out_path = LOGDIR / f"golden_{out['ts']}.json"
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print("saved:", out_path)

if __name__ == "__main__":
    main()
