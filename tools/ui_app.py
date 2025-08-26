import streamlit as st, pandas as pd, json
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.io.loader import load_table, detect_encoding, write_table
from app.excel_ops.clean import level1_clean
from app.excel_ops.dedupe import dedupe

st.set_page_config(page_title="Smart Excel Copilot", layout="wide")
st.title("🧹 Smart Excel Copilot — M0.5/M1 미니 UI")

path = st.text_input("입력 파일 경로(.csv/.xlsx)", value="data/goldensets/s01_mixed_currency.csv")
sheet = st.text_input("시트명(옵션)", value="")
col1, col2, col3 = st.columns(3)
with col1:
    opt_trim = st.checkbox("트림/공백 정규화", True)
with col2:
    opt_currency = st.checkbox("통화 분리+숫자화", True)
with col3:
    opt_date = st.checkbox("날짜 ISO(YYYY-MM-DD)", True)
opt_dedupe = st.checkbox("중복 제거(전체 열 기준)", False)

if st.button("미리보기"):
    enc = detect_encoding(path)
    df, _ = load_table(path, sheet=sheet or None, encoding=enc.get("encoding"))
    st.subheader("원본 미리보기")
    st.dataframe(df.head(30))
    df1 = level1_clean(df, trim=opt_trim, date_fmt="YYYY-MM-DD" if opt_date else "KEEP",
                       currency_split=opt_currency, drop_empty=True)
    if opt_dedupe:
        df1, info = dedupe(df1, keys=[], keep="last")
        st.caption(f"중복 제거 요약: {json.dumps(info, ensure_ascii=False)}")
    st.subheader("전처리 결과 미리보기")
    st.dataframe(df1.head(30))
    st.session_state["df_preview"] = df1

if "df_preview" in st.session_state:
    out_path = st.text_input("저장 경로", value="data/out/ui_cleaned.xlsx")
    if st.button("저장"):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        write_table(st.session_state["df_preview"], out_path, sheet="정리본")
        st.success(f"저장 완료: {out_path}")
