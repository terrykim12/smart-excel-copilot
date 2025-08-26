import sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import time
import json
import numpy as np
import pandas as pd
from pathlib import Path

from app.excel_ops.clean import level1_clean
from app.excel_ops.dedupe import dedupe
from app.core.profile import profile_dataframe

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data' / 'bench'
LOGS_DIR = ROOT / 'logs'
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def synth_data(n_rows: int = 200_000, dup_ratio: float = 0.1) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    ids = np.arange(n_rows)
    dup_count = int(n_rows * dup_ratio)
    if dup_count > 0:
        ids[:dup_count] = ids[rng.integers(low=0, high=n_rows - dup_count, size=dup_count)]
    rng.shuffle(ids)

    dates = pd.to_datetime('2024-01-01') + pd.to_timedelta(rng.integers(0, 200, size=n_rows), unit='D')
    date_str = np.where(
        rng.random(n_rows) < 0.33,
        dates.strftime('%Y-%m-%d'),
        np.where(rng.random(n_rows) < 0.5, dates.strftime('%Y/%m/%d'), dates.strftime('%Y.%m.%d'))
    )

    amounts = rng.normal(100_000, 50_000, size=n_rows).round(0).astype(int)
    amount_str = np.where(
        rng.random(n_rows) < 0.25,
        np.char.add('₩ ', np.char.mod('%d', amounts)),
        np.where(rng.random(n_rows) < 0.5, np.char.add('KRW ', np.char.mod('%d', amounts)), np.char.mod('%d원', amounts))
    )

    def with_comma(x: str) -> str:
        digits = ''.join(ch for ch in x if ch.isdigit())
        return x.replace(digits, f"{int(digits):,}")

    amount_str = np.vectorize(with_comma)(amount_str)

    active_vals = np.where(rng.random(n_rows) < 0.5, 'Y', 'N')
    city_pool = np.array(['서울', '부산', '대구', '인천', '광주', '대전'])
    cities = city_pool[rng.integers(0, len(city_pool), size=n_rows)]

    df = pd.DataFrame({
        '거래ID': ids,
        '주문일': date_str,
        '업데이트일': (pd.to_datetime(dates) + pd.to_timedelta(rng.integers(0, 86_400, size=n_rows), unit='s')).astype(str),
        '금액': amount_str,
        '도시': cities,
        '활성': active_vals,
        '메모': np.where(rng.random(n_rows) < 0.3, '', '메모')
    })
    return df


def timeit(fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    dt = time.perf_counter() - t0
    return result, dt


def run(n_rows: int = 200_000):
    print(f"[bench] generating synthetic data: {n_rows} rows ...", flush=True)
    df, t_gen = timeit(synth_data, n_rows)
    print(f"[bench] data generated in {t_gen:.2f}s", flush=True)

    print("[bench] profiling ...", flush=True)
    profile, t_prof = timeit(profile_dataframe, df, 100000)
    print(f"[bench] profile done in {t_prof:.2f}s, cols={len(profile['columns'])}", flush=True)

    print("[bench] cleaning (level1) ...", flush=True)
    df_clean, t_clean = timeit(level1_clean, df, True, 'YYYY-MM-DD', True, True)
    print(f"[bench] clean done in {t_clean:.2f}s, shape={df_clean.shape}", flush=True)
    print("[bench] columns after clean:", list(df_clean.columns), flush=True)

    print("[bench] dedupe ...", flush=True)
    # dedupe는 내부적으로 키/정렬 기준을 정규화하여 매핑함
    df_dedup, t_dedupe = timeit(dedupe, df_clean, ['거래id'], 'last_by:업데이트일')
    print(f"[bench] dedupe done in {t_dedupe:.2f}s, rows={len(df_dedup)}", flush=True)

    out = {
        'rows': int(n_rows),
        't_generate_s': round(t_gen, 3),
        't_profile_s': round(t_prof, 3),
        't_clean_s': round(t_clean, 3),
        't_dedupe_s': round(t_dedupe, 3),
        'rows_after_clean': int(len(df_clean)),
        'rows_after_dedupe': int(len(df_dedup)),
    }

    ts = int(time.time())
    out_path = DATA_DIR / f'bench_{n_rows}_{ts}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    last_path = LOGS_DIR / 'bench_last.json'
    with open(last_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"[bench] saved: {out_path}")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--rows', type=int, default=200_000)
    args = ap.parse_args()
    run(args.rows)
