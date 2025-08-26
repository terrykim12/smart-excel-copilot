#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
import json
from app.io.loader import load_table, detect_encoding
from app.core.utils import ensure_df
from app.report.template import build_report


def main():
    p = argparse.ArgumentParser(description="Generate Excel report (cover/KPI/sample/pivot+chart)")
    p.add_argument("--path", required=True)
    p.add_argument("--sheet", default=None)
    p.add_argument("--out", default="data/report/report.xlsx")
    p.add_argument("--title", default="월별 카테고리 매출 보고서")
    p.add_argument("--period", default="최근 기간")
    p.add_argument("--owner", default="Excel Copilot")
    p.add_argument("--chart", default="bar")
    p.add_argument("--pdf", action="store_true")
    args = p.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    enc = detect_encoding(args.path)
    result = load_table(args.path, sheet=args.sheet, encoding=enc.get("encoding"))

    if isinstance(result, tuple):
        df_dict, meta = result
    else:
        df_dict, meta = result, {}

    if isinstance(df_dict, dict):
        if args.sheet and args.sheet in df_dict:
            df = df_dict[args.sheet]
        else:
            first_sheet = list(df_dict.keys())[0]
            df = df_dict[first_sheet]
            print(f"[debug] first sheet selected: {first_sheet}")
    else:
        df = df_dict

    df = ensure_df(df)

    rep = build_report(
        df,
        args.out,
        title=args.title,
        period=args.period,
        owner=args.owner,
        chart_type=args.chart,
        rows=("날짜", "카테고리"),
        values=(("금액", "sum"),)
    )

    print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))

    if args.pdf:
        try:
            from app.report.pdf import xlsx_to_pdf_com
            pdf_path = Path(args.out).with_suffix(".pdf")
            ok = xlsx_to_pdf_com(args.out, str(pdf_path))
            if ok:
                print(json.dumps({"pdf": str(pdf_path)}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"pdf_error": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
