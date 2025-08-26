# tools/ui_copilot.py
from __future__ import annotations
import io, json, os, traceback
from pathlib import Path

import pandas as pd
import streamlit as st

# 프로젝트 모듈
from app.io.loader import load_table, write_table, detect_encoding
from app.core.profile import profile_dataframe
from app.excel_ops.clean import level1_clean
from app.excel_ops.dedupe import dedupe
from app.excel_ops.impute import impute as do_impute
from app.excel_ops.outlier import outlier as do_outlier
from app.validate.dsl import validate as dsl_validate
from app.autoexcel.intent import parse as nl_parse

# 선택적: Fallback/COM 엔진 로드
try:
    from app.autoexcel.engines_fallback import create_pivot_from_df, add_chart
except Exception:  # pragma: no cover
    create_pivot_from_df = add_chart = None

try:
    from app.autoexcel.engines_com import create_pivot_chart
    HAS_COM = True
except Exception:
    HAS_COM = False

st.set_page_config(page_title="Smart Excel Copilot", layout="wide")
st.markdown(
    """
    <style>
      .badge-ok{background:#16a34a;color:#fff;padding:2px 8px;border-radius:999px}
      .badge-warn{background:#d97706;color:#fff;padding:2px 8px;border-radius:999px}
      .muted{color:#64748b}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# 공용 유틸
# ---------------------------
def _load_df(path: str|None, upload) -> tuple[pd.DataFrame, dict]:
    if upload is not None:
        # 업로드 파일 메모리에 저장 후 로더로 전달
        tmp = Path("data/_uploads"); tmp.mkdir(parents=True, exist_ok=True)
        p = tmp / upload.name
        p.write_bytes(upload.getbuffer())
        enc = detect_encoding(str(p))
        df, meta = load_table(str(p), encoding=enc.get("encoding"))
        meta["path"] = str(p)
        return df, meta
    if path:
        enc = detect_encoding(path)
        df, meta = load_table(path, encoding=enc.get("encoding"))
        meta["path"] = path
        return df, meta
    raise ValueError("파일 경로를 입력하거나 파일을 업로드해 주세요.")

def _download_df_button(df: pd.DataFrame, filename: str, label="CSV 다운로드"):
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button(label, data=buf.getvalue(), file_name=filename, mime="text/csv")

def _save_xlsx_and_download(df: pd.DataFrame, path: str, sheet="정리본"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_table(df, path, sheet=sheet)
    with open(path, "rb") as f:
        st.download_button("엑셀 파일 다운로드", f.read(), file_name=Path(path).name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def _pretty_json(obj):
    st.code(json.dumps(obj, ensure_ascii=False, indent=2), language="json")

# ---------------------------
# 사이드바: 입력 소스
# ---------------------------
with st.sidebar:
    st.header("📂 입력")
    path = st.text_input("파일 경로(.csv/.xlsx)", value="data/goldensets/s01_mixed_currency.csv")
    upload = st.file_uploader("또는 파일 업로드", type=["csv","xlsx"])
    st.caption("경로 또는 업로드 중 하나만 사용하세요.")
    st.divider()
    st.header("⚙️ 설정")
    parser = st.selectbox("자연어 파서", ["auto","rule","llm"], index=0)
    engine = st.selectbox("엑셀 엔진", ["fallback","com" if HAS_COM else "fallback"], index=0)
    st.caption(f"COM 엔진 사용 가능: {'예' if HAS_COM else '아니오'}")

# ---------------------------
# 탭
# ---------------------------
tab_pro, tab_pre, tab_auto, tab_val, tab_log, tab_watch = st.tabs(
    ["🔎 프로파일링", "🧹 전처리", "📊 엑셀 자동화", "✅ 검증", "📜 로그/리포트", "👁️ 폴더 감시"]
)

# ---------------------------
# 프로파일링
# ---------------------------
with tab_pro:
    st.subheader("🔎 데이터 프로파일링")
    if st.button("프로파일 생성"):
        try:
            df, meta = _load_df(path, upload)
            prof = profile_dataframe(df)
            st.success("프로파일 생성 완료")
            st.write(f"행/열: **{len(df)} x {df.shape[1]}**")
            cols = prof.get("columns", [])
            for c in cols:
                with st.expander(f"열: {c.get('name')}"):
                    _pretty_json(c)
            with st.expander("전체 프로파일 JSON"):
                _pretty_json(prof)
            st.session_state["last_df"] = df
            st.session_state["last_meta"] = meta
        except Exception as e:
            st.error(str(e))
            st.exception(e)

# ---------------------------
# 전처리
# ---------------------------
with tab_pre:
    st.subheader("🧹 전처리 (Level1 + Dedupe/Impute/Outlier)")
    c1, c2, c3, c4 = st.columns(4)
    with c1: opt_trim = st.checkbox("트림/공백 정리", True)
    with c2: opt_currency = st.checkbox("통화 분리+숫자화", True)
    with c3: opt_date = st.checkbox("날짜 ISO(YYYY-MM-DD)", True)
    with c4: opt_drop_empty = st.checkbox("빈 행/열 제거", True)

    st.markdown("**중복 제거**")
    c5, c6 = st.columns(2)
    with c5: dedupe_keys = st.text_input("키(쉼표로 구분, 비우면 전체 열 비교)", value="거래ID")
    with c6: keep_rule = st.text_input("보존 정책(first/last/last_by:업데이트일)", value="last")

    st.markdown("**결측/이상치**")
    impute_rule = st.text_input('결측 규칙 예: `median:금액;zero:수량`', value="")
    outlier_rule = st.text_input('이상치 규칙 예: `iqr_clip:금액@k=1.5`', value="")

    st.markdown("**게이트 DSL (저장 차단 조건)**")
    c7, c8 = st.columns(2)
    with c7: gate_path = st.text_input("DSL 파일 경로(YAML/JSON, 선택)", value="")
    with c8: gate_threshold = st.slider("통과율 임계값", 0.0, 1.0, 1.0, 0.05)

    if st.button("미리보기"):
        try:
            df, meta = _load_df(path, upload)
            df1 = level1_clean(df, trim=opt_trim, date_fmt=("YYYY-MM-DD" if opt_date else "KEEP"),
                               currency_split=opt_currency, drop_empty=opt_drop_empty)
            info = {}
            # dedupe
            if dedupe_keys.strip():
                keys = [k.strip() for k in dedupe_keys.split(",") if k.strip()]
                df1, info = dedupe(df1, keys=keys, keep=keep_rule)
            # impute
            if impute_rule.strip():
                def parse_kv(s):
                    out=[]
                    for t in s.split(";"):
                        t=t.strip()
                        if not t: continue
                        m,c = t.split(":",1)
                        out.append({"method":m.strip(),"col":c.strip()})
                    return out
                df1, rep_i = do_impute(df1, parse_kv(impute_rule))
                st.caption(f"결측 대체 리포트: {json.dumps(rep_i, ensure_ascii=False)}")
            # outlier
            if outlier_rule.strip():
                def parse_ol(s):
                    out=[]
                    for t in s.split(";"):
                        t=t.strip()
                        if not t: continue
                        head,*attrs = t.split("@")
                        m,c = head.split(":",1)
                        item={"method":m.strip(),"col":c.strip()}
                        for a in attrs:
                            for kv in a.split(","):
                                if "=" in kv:
                                    k,v = kv.split("=",1)
                                    try: v = float(v) if any(x in v for x in ".0123456789") else v
                                    except: pass
                                    item[k.strip()]=v
                        out.append(item)
                    return out
                df1, rep_o = do_outlier(df1, parse_ol(outlier_rule))
                st.caption(f"이상치 처리 리포트: {json.dumps(rep_o, ensure_ascii=False)}")

            st.success("전처리 미리보기 완료")
            st.dataframe(df1.head(30))
            st.session_state["preview_df"] = df1
            st.session_state["preview_meta"] = meta
            if info:
                st.caption(f"중복 제거 요약: {json.dumps(info, ensure_ascii=False)}")
        except Exception as e:
            st.error("전처리 실패")
            st.exception(e)

    if "preview_df" in st.session_state and st.button("저장(게이트 검사 포함)"):
        try:
            df1 = st.session_state["preview_df"]
            # 게이트 검사
            if gate_path.strip():
                with open(gate_path, "r", encoding="utf-8") as f:
                    import yaml
                    spec = yaml.safe_load(f)
                rep = dsl_validate(df1, spec)
                details = rep.get("details", [])
                pass_ratio = (sum(1 for d in details if d.get("ok")) / max(1, len(details)))
                st.caption(f"게이트 결과: pass_ratio={pass_ratio:.3f}")
                _pretty_json(rep)
                if pass_ratio < float(gate_threshold):
                    st.error(f"통과율 {pass_ratio:.3f} < 임계값 {gate_threshold} → 저장 차단")
                    st.stop()

            # 저장
            out_path = "data/out/ui_cleaned.xlsx"
            _save_xlsx_and_download(df1, out_path)
            st.success(f"저장 완료: {out_path}")
        except Exception as e:
            st.error("저장 실패")
            st.exception(e)

# ---------------------------
# 엑셀 자동화 (자연어)
# ---------------------------
with tab_auto:
    st.subheader("📊 자연어 → 피벗/차트")
    ask = st.text_input("요청", value="월별 카테고리 매출 피벗 만들고 막대차트, 지역은 서울과 부산만")
    out_xlsx = st.text_input("출력 경로", value="data/automation/auto_out.xlsx")
    
    # MoM/YTD 옵션 추가
    add_mom_ytd = st.checkbox("MoM(전월대비) + YTD(누계) 열 자동 추가", True)
    
    if st.button("생성"):
        try:
            df, meta = _load_df(path, upload)
            intent = nl_parse(ask, columns=df.columns, parser=parser)
            st.caption(f"의도: {intent.model_dump() if hasattr(intent,'model_dump') else intent.__dict__}")
            Path(out_xlsx).parent.mkdir(parents=True, exist_ok=True)

            if engine == "com" and HAS_COM:
                # 원본을 xlsx로 보장
                tmp_src = "data/automation/_tmp_src.xlsx"
                write_table(df, tmp_src, sheet="원본")
                rows = intent.rows or ["월","카테고리"]
                vals = intent.values or [("금액","sum")]
                create_pivot_chart(tmp_src, out_xlsx, "원본", "피벗_결과", rows, vals, chart_type=intent.chart or "bar")
            else:
                rows = intent.rows or ["월","카테고리"]
                vals = intent.values or [("금액","sum")]
                filters = getattr(intent, "filters", None)
                shape = create_pivot_from_df(df, out_xlsx, "03_피벗", rows, vals, filters=filters)
                if intent.chart:
                    add_chart(out_xlsx, "03_피벗", title="자동 차트", chart_type=intent.chart)
                st.caption(f"피벗 shape: {shape}")

            # MoM/YTD 열 추가
            if add_mom_ytd:
                try:
                    from app.autoexcel.formulas import add_mom_ytd_columns
                    add_mom_ytd_columns(out_xlsx, "03_피벗")
                    st.success("✅ MoM/YTD 열 추가 완료")
                except Exception as e:
                    st.warning(f"⚠️ MoM/YTD 열 추가 실패: {e}")

            st.success(f"완료: {out_xlsx}")
            with open(out_xlsx, "rb") as f:
                st.download_button("보고서 다운로드", f.read(), file_name=Path(out_xlsx).name)
        except Exception as e:
            st.error("엑셀 자동화 실패")
            st.exception(e)

# ---------------------------
# 검증 DSL
# ---------------------------
with tab_val:
    st.subheader("✅ 검증(DSL)")
    dsl_path = st.text_input("DSL 경로(YAML/JSON)", value="examples/validation_example.yaml")
    if st.button("검증 실행"):
        try:
            df, meta = _load_df(path, upload)
            import yaml
            spec = yaml.safe_load(open(dsl_path, "r", encoding="utf-8"))
            rep = dsl_validate(df, spec)
            _pretty_json(rep)
            ok = rep.get("summary",{}).get("ok", False)
            badge = '<span class="badge-ok">PASS</span>' if ok else '<span class="badge-warn">FAIL</span>'
            st.markdown(f"결과: {badge}", unsafe_allow_html=True)
        except Exception as e:
            st.error("검증 실패")
            st.exception(e)

# ---------------------------
# 로그/리포트
# ---------------------------
with tab_log:
    st.subheader("📜 로그/리포트")
    # KPI 최근 결과 표시(있다면)
    kpi = Path("logs/kpi_last.json")
    if kpi.exists():
        st.markdown("**최근 KPI**")
        st.code(kpi.read_text(encoding="utf-8"), language="json")
        st.download_button("KPI JSON 다운로드", data=kpi.read_bytes(), file_name=kpi.name)
    else:
        st.caption("KPI 로그가 아직 없습니다. tools/eval_kpi.py를 실행해 보세요.")
    # 최근 골든셋 요약
    gdir = Path("logs/golden_runs")
    if gdir.exists():
        latest = sorted(gdir.glob("golden_*.json"))[-1:]
        for p in latest:
            st.markdown("**최근 골든셋 결과**")
            st.code(p.read_text(encoding="utf-8"), language="json")
            st.download_button("골든셋 요약 다운로드", data=p.read_bytes(), file_name=p.name)

# ---------------------------
# 폴더 감시 (Watch)
# ---------------------------
with tab_watch:
    st.subheader("👁️ 폴더 감시 → 자동 보고서 생성")
    
    watch_dir = st.text_input("감시할 폴더", value="data/incoming")
    st.caption("CSV/XLSX 파일이 이 폴더에 떨어지면 자동으로 보고서가 생성됩니다.")
    
    if st.button("감시 시작"):
        try:
            # 폴더 생성
            Path(watch_dir).mkdir(parents=True, exist_ok=True)
            
            # 감시 프로세스 시작
            import subprocess
            cmd = [sys.executable, "tools/watch_run.py", "--dir", watch_dir]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            st.success(f"폴더 감시 시작: {watch_dir}")
            st.info("이제 폴더에 CSV/XLSX 파일을 드롭하면 자동으로 보고서가 생성됩니다.")
            
            # 프로세스 상태 표시
            if process.poll() is None:
                st.caption("✅ 감시 프로세스 실행 중")
            else:
                st.caption("❌ 감시 프로세스 종료됨")
                
        except Exception as e:
            st.error(f"감시 시작 실패: {e}")
            st.exception(e)
    
    # 감시 중인 폴더 내용 표시
    if Path(watch_dir).exists():
        st.markdown("**감시 폴더 내용**")
        files = list(Path(watch_dir).glob("*"))
        if files:
            for f in files:
                st.write(f"📄 {f.name} ({f.stat().st_size} bytes)")
        else:
            st.caption("폴더가 비어있습니다. CSV/XLSX 파일을 드롭해보세요.")
    
    # 자동 생성된 보고서 목록
    report_dir = Path("data/report")
    if report_dir.exists():
        st.markdown("**자동 생성된 보고서**")
        auto_reports = list(report_dir.glob("auto_*.xlsx"))
        if auto_reports:
            for r in auto_reports:
                st.write(f"📊 {r.name} ({r.stat().st_size} bytes)")
                with open(r, "rb") as f:
                    st.download_button(f"다운로드 {r.name}", f.read(), file_name=r.name)
        else:
            st.caption("아직 자동 생성된 보고서가 없습니다.")

