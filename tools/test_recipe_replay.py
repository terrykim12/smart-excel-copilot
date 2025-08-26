import json, subprocess, sys, time, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECIPE = ROOT / "recipes" / "clean_dedupe_weekly.yaml"
OUT = ROOT / "data" / "out" / "weekly.cleaned.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr

def main():
    t0 = time.time()
    code, so, se = run([sys.executable, "-m", "app.cli", "replay", "--recipe", str(RECIPE), "--apply"])
    dt = time.time() - t0
    ok = (code == 0) and OUT.exists()
    print(json.dumps({
        "recipe": str(RECIPE),
        "out_exists": OUT.exists(),
        "returncode": code,
        "seconds": round(dt, 3),
    }, ensure_ascii=False, indent=2))
    if not ok:
        print("STDOUT:\n", so)
        print("STDERR:\n", se)
        sys.exit(1)

if __name__ == "__main__":
    main()
