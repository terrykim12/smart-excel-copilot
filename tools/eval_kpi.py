import json, time, pathlib, sys
import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.io.loader import load_table, detect_encoding
from app.excel_ops.clean import level1_clean
from app.excel_ops.dedupe import dedupe

OUTDIR = ROOT / "logs"; OUTDIR.mkdir(parents=True, exist_ok=True)

def _metrics(df: pd.DataFrame) -> dict:
    n = len(df)
    miss = float(df.isna().mean().mean())
    dup_all = float((n - len(df.drop_duplicates()))/max(n,1))
    # 타입 힌트: 숫자/날짜로 해석된 비율(대략치)
    num_ratio = float((df.apply(pd.api.types.is_numeric_dtype)).mean())
    date_ratio = float(df.select_dtypes(include="object").apply(
        lambda s: pd.to_datetime(s, errors="coerce").notna().mean() if s.dtype=="object" else 0
    ).mean())
    return {"rows": n, "missing_rate": round(miss,4), "dup_rate": round(dup_all,4),
            "numeric_col_rate": round(num_ratio,4), "date_parse_rate_guess": round(date_ratio,4)}

def run_one(path: str, sheet=None) -> dict:
    enc = detect_encoding(path)
    df, _ = load_table(path, sheet=sheet, encoding=enc.get("encoding"))
    m0 = _metrics(df)
    t0 = time.perf_counter()
    df1 = level1_clean(df, trim=True, date_fmt="YYYY-MM-DD", currency_split=True, drop_empty=True)
    t_clean = time.perf_counter() - t0
    # dedupe(옵션): 열 이름 다양성 때문에 전체 중복으로 측정
    t1 = time.perf_counter()
    df2, _ = dedupe(df1, keys=[], keep="last")  # ALL 열 기준
    t_dedup = time.perf_counter() - t1
    m1 = _metrics(df2)
    return {"file": path, "before": m0, "after": m1,
            "t_clean_s": round(t_clean,3), "t_dedupe_s": round(t_dedup,3)}

def main():
    gs = (ROOT / "data" / "goldensets").glob("*.*")
    results = [run_one(str(p)) for p in gs if p.suffix.lower() in (".csv",".xlsx")]
    out = {"ts": int(time.time()), "results": results}
    (OUTDIR / "kpi_last.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

