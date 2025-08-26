from __future__ import annotations
import re, json, pandas as pd
from typing import Dict, Any, List, Tuple

def validate(df: pd.DataFrame, spec: Dict[str, Any]) -> Dict[str, Any]:
    checks = spec.get("checks", [])
    report: List[Dict[str, Any]] = []
    for c in checks:
        if "unique" in c:
            for col in c["unique"]:
                ok = df[col].is_unique if col in df.columns else False
                report.append({"check":"unique","col":col,"ok":bool(ok)})
        if "required" in c:
            for col in c["required"]:
                ok = (col in df.columns) and df[col].notna().all()
                report.append({"check":"required","col":col,"ok":bool(ok), "missing": int(df[col].isna().sum()) if col in df.columns else None})
        if "regex" in c:
            col = c["regex"]["column"]; pat = re.compile(c["regex"]["pattern"])
            if col in df.columns:
                bad = df[col].astype("string").fillna("").str.match(pat).fillna(False) == False
                n_bad = int(bad.sum())
                report.append({"check":"regex","col":col,"ok": n_bad==0, "fails": n_bad})
            else:
                report.append({"check":"regex","col":col,"ok":False,"error":"col_not_found"})
        if "range" in c:
            col = c["range"]["column"]; lo = c["range"].get("min"); hi = c["range"].get("max")
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce")
                bad = ((s < lo) | (s > hi)).fillna(False)
                n_bad = int(bad.sum())
                report.append({"check":"range","col":col,"ok": n_bad==0, "fails": n_bad, "min":lo,"max":hi})
            else:
                report.append({"check":"range","col":col,"ok":False,"error":"col_not_found"})
    return {"summary": {"ok": all(x.get("ok", False) for x in report)}, "details": report}
