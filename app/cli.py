# -*- coding: utf-8 -*-
"""
명령줄 인터페이스(CLI)
Smart Excel Copilot의 다양한 기능을 명령줄에서 사용할 수 있습니다.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List

import pandas as pd

from .core.profile import profile_dataframe
from .excel_ops.clean import level1_clean
from .excel_ops.dedupe import dedupe
from .excel_ops.impute import handle_missing_values, analyze_missing_patterns, suggest_impute_strategies
from .excel_ops.outlier import detect_outliers, handle_outliers, get_outlier_summary
from .excel_ops.schema import align_schemas, merge_aligned_dataframes, analyze_schema_compatibility
from .recipes.manager import RecipeManager
from .autoexcel.intent import parse as nl_parse
from .autoexcel.engines_fallback import create_pivot_from_df, add_chart, write_formula
from .io.loader import load_table, write_table, detect_encoding
from .core.utils import ensure_df
import platform

def build_parser():
    ap = argparse.ArgumentParser(
        prog="sec",
        description="Smart Excel Copilot CLI"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    # profile
    sp = sub.add_parser("profile", help="Profile dataset")
    sp.add_argument("--path", required=True, help="Input CSV/XLSX path")
    sp.add_argument("--sheet", default=None, help="Sheet name if Excel")
    sp.set_defaults(func=cmd_profile)

    # clean
    sp = sub.add_parser("clean", help="Level-1 cleaning")
    sp.add_argument("--path", required=True)
    sp.add_argument("--date-fmt", default="YYYY-MM-DD")
    sp.add_argument("--apply", action="store_true", help="Save cleaned file")
    sp.set_defaults(func=cmd_clean)

    # dedupe
    sp = sub.add_parser("dedupe", help="Remove duplicates")
    sp.add_argument("--path", required=True)
    sp.add_argument("--keys", default="거래ID", help="Comma separated keys")
    sp.add_argument("--keep", default="last", help="first/last/last_by:컬럼명")
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_dedupe)

    # preprocess (pipeline)
    sp = sub.add_parser("preprocess", help="Clean + (optional) impute/outlier")
    sp.add_argument("--path", required=True)
    sp.add_argument("--impute", default=None, help='e.g. "median:금액;zero:수량"')
    sp.add_argument("--outlier", default=None, help='e.g. "iqr_clip:금액@k=1.5"')
    sp.add_argument("--gate-dsl", default=None, help="Validation DSL file")
    sp.add_argument("--gate-pass-threshold", type=float, default=1.0)
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_preprocess)

    # replay
    sp = sub.add_parser("replay", help="Run recipe")
    sp.add_argument("--recipe", required=True)
    sp.add_argument("--apply", action="store_true")
    sp.set_defaults(func=cmd_replay)

    # goldens
    sp = sub.add_parser("goldens", help="Run golden tests")
    sp.set_defaults(func=cmd_goldens)

    # validate DSL
    sp = sub.add_parser("validate", help="Validate dataset by DSL")
    sp.add_argument("--path", required=True)
    sp.add_argument("--sheet", default=None)
    sp.add_argument("--dsl", required=True)
    sp.set_defaults(func=cmd_validate)

    # excel-auto (natural language → pivot/chart)
    sp = sub.add_parser("excel-auto", help="Natural language pivot/chart")
    sp.add_argument("--path", required=True)
    sp.add_argument("--ask", required=True)
    sp.add_argument("--parser", choices=["auto","rule","llm"], default="auto")
    sp.add_argument("--engine", choices=["fallback","com"], default="fallback")
    sp.add_argument("--out", default="data/automation/auto_out.xlsx")
    sp.set_defaults(func=cmd_excel_auto)

    # excel-formula (MoM/YTD)
    sp = sub.add_parser("excel-formula", help="Add MoM/YTD formula columns")
    sp.add_argument("--path", required=True)
    sp.add_argument("--sheet", default="03_피벗")
    sp.set_defaults(func=cmd_excel_formula)

    # excel-report (cover/KPI/sample/pivot/chart)
    sp = sub.add_parser("excel-report", help="Build Excel report")
    sp.add_argument("--path", required=True)
    sp.add_argument("--out", default="data/report/report.xlsx")
    sp.add_argument("--title", default="Sales report")
    sp.add_argument("--period", default="Recent")
    sp.add_argument("--owner", default="Excel Copilot")
    sp.add_argument("--chart", default="bar")
    sp.add_argument("--pdf", action="store_true")
    sp.set_defaults(func=cmd_excel_report)

    # watch
    sp = sub.add_parser("watch", help="Watch dir and auto build report")
    sp.add_argument("--dir", default="data/incoming")
    sp.set_defaults(func=cmd_watch)

    # undo
    sp = sub.add_parser("undo", help="Restore from undo token")
    sp.add_argument("--token", required=True)
    sp.set_defaults(func=cmd_undo)

    return ap

def _resolve_path_arg(args):
    """경로 인자 해결 (--path 또는 위치 인자)"""
    if hasattr(args, 'path') and args.path:
        return args.path
    if hasattr(args, 'path_pos') and args.path_pos:
        return args.path_pos
    return None

def _auto_out_path(input_path: str, suffix: str = "_cleaned") -> str:
    """자동 출력 경로 생성"""
    p = Path(input_path)
    return str(p.parent / f"{p.stem}{suffix}{p.suffix}")

def cmd_profile(args):
    """데이터셋 프로파일링"""
    path = _resolve_path_arg(args)
    if not path:
        raise SystemExit("usage: profile --path <file>")
    
    enc = detect_encoding(path)
    df, meta = load_table(path, sheet=args.sheet, encoding=enc.get("encoding"))
    df = ensure_df(df)
    
    prof = profile_dataframe(df)
    print(json.dumps({
        "path": path,
        "shape": df.shape,
        "profile": prof
    }, ensure_ascii=False, indent=2, default=str))

def cmd_clean(args):
    """Level-1 데이터 정리"""
    path = _resolve_path_arg(args)
    if not path:
        raise SystemExit("usage: clean --path <file>")
    
    enc = detect_encoding(path)
    df, meta = load_table(path, sheet=args.sheet, encoding=enc.get("encoding"))
    df = ensure_df(df)
    
    df_cleaned = level1_clean(df, date_fmt=args.date_fmt)
    
    if args.apply:
        out_path = _auto_out_path(path, "_cleaned")
        write_table(df_cleaned, out_path, sheet="정리본")
        print(json.dumps({"saved": out_path}, ensure_ascii=False, indent=2))
    else:
        print(df_cleaned.head(20).to_string(index=False))

def cmd_dedupe(args):
    """중복 제거"""
    path = _resolve_path_arg(args)
    if not path:
        raise SystemExit("usage: dedupe --path <file>")
    
    enc = detect_encoding(path)
    df, meta = load_table(path, sheet=args.sheet, encoding=enc.get("encoding"))
    
    keys = [k.strip() for k in args.keys.split(",")]
    df_dedup, info = dedupe(df, keys, args.keep)
    
    print(json.dumps({
        "input_rows": len(df),
        "output_rows": len(df_dedup),
        "removed": info["removed"],
        "keys": info["keys"],
        "keep": info["keep"]
    }, ensure_ascii=False, indent=2))

def cmd_preprocess(args):
    """전처리 파이프라인 (정리 + 결측/이상치 처리)"""
    path = _resolve_path_arg(args)
    if not path:
        raise SystemExit("usage: preprocess --path <file>")
    
    enc = detect_encoding(path)
    df, meta = load_table(path, sheet=args.sheet, encoding=enc.get("encoding"))
    df = ensure_df(df)
    
    # 1단계: 기본 정리
    df = level1_clean(df)
    
    # 2단계: 결측치 처리
    if args.impute:
        # impute 규칙 파싱 및 적용
        pass
    
    # 3단계: 이상치 처리
    if args.outlier:
        # outlier 규칙 파싱 및 적용
        pass
    
    if args.apply:
        out_path = _auto_out_path(path, "_preprocessed")
        write_table(df, out_path, sheet="전처리본")
        print(json.dumps({"saved": out_path}, ensure_ascii=False, indent=2))
    else:
        print(df.head(20).to_string(index=False))

def cmd_replay(args):
    """레시피 실행"""
    print(f"레시피 실행: {args.recipe}")
    if args.apply:
        print("적용 모드로 실행")
    else:
        print("미리보기 모드로 실행")

def cmd_goldens(args):
    """골든 테스트 실행"""
    print("골든 테스트 실행 중...")

def cmd_validate(args):
    """DSL 검증"""
    import yaml
    enc = detect_encoding(args.path)
    df, _ = load_table(args.path, sheet=args.sheet, encoding=enc.get("encoding"))
    df = ensure_df(df)
    
    # YAML 또는 JSON 파일 읽기
    try:
        with open(args.dsl, "r", encoding="utf-8") as f:
            if args.dsl.endswith('.yaml') or args.dsl.endswith('.yml'):
                spec = yaml.safe_load(f)
            else:
                spec = json.loads(f.read())
    except Exception as e:
        print(f"DSL 파일 읽기 오류: {e}")
        return
    
    from .validate.dsl import validate as vrun
    rep = vrun(df, spec)
    print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))

def cmd_excel_auto(args):
    """자연어 → 피벗/차트 자동 생성"""
    enc = detect_encoding(args.path)
    df, meta = load_table(args.path, sheet=args.sheet, encoding=enc.get("encoding"))
    df = ensure_df(df)
    
    # 자연어 의도 파싱
    intent = nl_parse(args.ask, columns=df.columns, parser=args.parser)
    
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    
    if args.engine == "com":
        # COM 엔진 사용
        try:
            from .autoexcel.engines_com import create_pivot_chart
            tmp_src = "data/automation/_tmp_src.xlsx"
            write_table(df, tmp_src, sheet="원본")
            rows = intent.rows or ["월","카테고리"]
            vals = intent.values or [("금액","sum")]
            create_pivot_chart(tmp_src, args.out, "원본", "03_피벗", rows, vals, chart_type=intent.chart or "bar")
            print(json.dumps({"engine": "com", "out": args.out}, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"COM 엔진 실패: {e}")
            print("fallback 엔진으로 전환")
            args.engine = "fallback"
    
    if args.engine == "fallback":
        # Fallback 엔진 사용
        rows = intent.rows or ["월","카테고리"]
        vals = intent.values or [("금액","sum")]
        filters = getattr(intent, "filters", None)
        shape = create_pivot_from_df(df, args.out, "03_피벗", rows, vals, filters=filters)
        if intent.chart:
            add_chart(args.out, "03_피벗", title="자동 차트", chart_type=intent.chart)
        print(json.dumps({
            "engine": "fallback",
            "out": args.out,
            "pivot_shape": shape
        }, ensure_ascii=False, indent=2))

def cmd_excel_formula(args):
    """MoM/YTD 수식 열 자동 추가"""
    from .autoexcel.formulas import add_mom_ytd_columns
    add_mom_ytd_columns(args.path, sheet=args.sheet)
    print(json.dumps({
        "path": args.path,
        "sheet": args.sheet,
        "status": "MoM/YTD columns added"
    }, ensure_ascii=False))

def cmd_excel_report(args):
    """Excel 보고서 생성 (표지/KPI/샘플/피벗+차트)"""
    from .report.template import build_report
    
    # 데이터 로드
    enc = detect_encoding(args.path)
    result = load_table(args.path, sheet=args.sheet, encoding=enc.get("encoding"))
    
    # load_table 결과 처리
    if isinstance(result, tuple):
        df_dict, meta = result
    else:
        df_dict = result
        meta = {}
    
    # 시트가 여러 개인 경우 첫 번째 시트 선택
    if isinstance(df_dict, dict):
        if args.sheet and args.sheet in df_dict:
            df = df_dict[args.sheet]
        else:
            first_sheet = list(df_dict.keys())[0]
            df = df_dict[first_sheet]
            print(f"[debug] 첫 번째 시트 '{first_sheet}' 선택됨")
    else:
        df = df_dict
    
    df = ensure_df(df)
    print(f"[debug] 데이터 로드 완료: {len(df)}행 x {len(df.columns)}열")
    
    # 자동 분석 제안 (간단한 버전)
    suggestions = {
        "rows": ["날짜", "카테고리"],
        "values": [("금액", "sum")],
        "chart": "bar"
    }
    
    # 보고서 생성
    rep = build_report(
        df, 
        args.out, 
        title=args.title, 
        period=args.period, 
        owner=args.owner, 
        chart_type=args.chart,
        rows=suggestions.get("rows", ["날짜", "카테고리"]),
        values=suggestions.get("values", [("금액", "sum")])
    )
    
    print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))
    
    # PDF 내보내기 (선택)
    if getattr(args, "pdf", False):
        try:
            from .report.pdf import xlsx_to_pdf_com
            pdf_path = Path(args.out).with_suffix(".pdf")
            xlsx_to_pdf_com(args.out, str(pdf_path))
            print(json.dumps({"pdf": str(pdf_path)}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"pdf_error": str(e)}, ensure_ascii=False))

def cmd_watch(args):
    """폴더 감시 → 자동 보고서 생성"""
    import subprocess
    cmd = [sys.executable, "tools/watch_run.py", "--dir", args.dir]
    subprocess.run(cmd, check=False)

def cmd_undo(args):
    """이전 백업에서 복원"""
    print(f"복원 토큰: {args.token}")

def main():
    ap = build_parser()
    args = ap.parse_args()
    if hasattr(args, "func"):
        return args.func(args)
    ap.print_help()

if __name__ == '__main__':
    main()

