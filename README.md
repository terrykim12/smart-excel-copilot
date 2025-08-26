# Smart Excel Copilot

**v0.5.0-rc2** - LLM 폴백 + 자연어 필터 + COM 안정화 포함

Excel 데이터 전처리를 위한 Python 기반 도구입니다.

## 🚀 퀵스타트

### 필수 설정 (PowerShell에서 실행)
```bash
.\setup_console.ps1                    # 콘솔 한글 고정
.\install.ps1                          # 기본 패키지 설치
.\install_ollama.ps1                   # 자연어 파서 설정 (선택)
```

### 기본 기능 테스트
```bash
python -m app.cli profile --path data/goldensets/s01_mixed_currency.csv
python -m app.cli preprocess --path data/goldensets/s01_mixed_currency.csv --apply
python -m app.cli excel-auto --path data/goldensets/s01_mixed_currency.csv --ask "월별 카테고리 매출 피벗과 막대차트"
```

### 🌐 Streamlit UI 사용법

```bash
# PowerShell에서 실행
.\run_ui.ps1

# 또는 직접 실행
$env:PYTHONPATH=".;smart_excel_copilot"
streamlit run tools/ui_copilot.py
```

**UI 기능:**
- 🔎 **프로파일링**: 데이터 구조 및 통계 분석
- 🧹 **전처리**: 클린 + 중복/결측/이상치 처리 + 게이트 검증
- 📊 **엑셀 자동화**: 자연어 → 피벗/차트 생성
- ✅ **검증**: DSL 기반 데이터 품질 검사
- 📜 **로그/리포트**: KPI 및 실행 결과 확인

## 📋 프로젝트 개요

데이터 프로파일링 및 전처리를 위한 Python 도구입니다.

## 🚀 주요 기능

### M0.5 (현재 구현 완료)
- **데이터 프로파일링**: 타입 추론, 통계 분석, 샘플링
- **레벨 1 클리닝**: 열명 표준화, 공백 정리, 통화 분리, 날짜 표준화
- **중복 제거**: 다양한 보존 정책 지원

### M1 (스켈레톤 구현)
- **결측치 처리**: 다양한 전략 (평균, 중앙값, 최빈값 등)
- **이상치 처리**: IQR, Z-score, Isolation Forest
- **스키마 정렬**: 여러 파일의 스키마 자동 정렬 및 병합

### M2 (기본 구조)
- **레시피 시스템**: 전처리 작업 저장 및 재실행

### M3 (자연어 파서 + Excel COM 엔진)
- **자연어 의도 파싱**: 규칙 기반 + LLM 백업 (Ollama)
- **Excel COM 엔진**: Windows에서 실제 Excel로 피벗/차트 생성
- **하이브리드 파서**: 규칙 → LLM → 폴백 순서로 의도 해석

### M4 (KPI 자동화 + UI + CI)
- **KPI 자동 집계**: 결측률·중복률·타입 파싱율, 처리 시간 측정
- **Streamlit UI**: 파일 경로 입력 → 프로파일 요약 → 체크박스로 적용 → 미리보기 → 저장
- **CI 파이프라인**: GitHub Actions로 윈도우/우분투 매트릭스 빌드
- **필터·매핑 강화**: 자연어 필터 + 열명 자동 매핑으로 정확도 향상

## 📦 설치

### 기본 설치
```bash
pip install -r requirements.txt
```

### 자연어 파서 설정 (선택사항)
```bash
# PowerShell에서 실행
.\install_ollama.ps1

# 또는 수동으로
winget install Ollama.Ollama
ollama serve
ollama pull qwen2.5:3b-instruct

# 모델 변경
$env:SEC_LLM_MODEL="llama3.2:3b-instruct"  # 다른 모델 사용
ollama pull llama3.2:3b-instruct
```

### 콘솔 한글 설정
```bash
# PowerShell에서 실행
.\setup_console.ps1
```

### LLM 모델 환경변수 설정
```bash
# PowerShell에서 실행
.\set_env.ps1

# 또는 수동으로
$env:SEC_LLM_MODEL="qwen2.5:3b-instruct"
```

## 🎯 사용법

### 1. 기본 사용 (Python 모듈)

```python
from app.io.loader import load_table
from app.core.profile import profile_dataframe
from app.excel_ops.clean import level1_clean
from app.excel_ops.dedupe import dedupe

# 파일 로드
df = load_table('data/sample.csv')

# 프로파일링
profile = profile_dataframe(df)

# 클리닝
df_cleaned = level1_clean(df, currency_split=True, date_fmt='YYYY-MM-DD')

# 중복 제거
df_deduped = dedupe(df_cleaned, keys=['ID'], keep_policy='last_by:업데이트일')
```

### 2. 명령행 인터페이스 (CLI)

```bash
# 데이터 프로파일링
python -m app.cli profile data/sample.csv

# 데이터 클리닝
python -m app.cli clean data/sample.csv --apply --output cleaned.csv

# 중복 제거
python -m app.cli dedupe data/sample.csv --keys "ID,날짜" --keep last_by:업데이트일

# 결측치 처리
python -m app.cli impute data/sample.csv --strategy median --columns "수량,금액"

# 이상치 처리
python -m app.cli outlier data/sample.csv --method iqr --action clip

# 스키마 정렬 및 병합
python -m app.cli schema data1.csv data2.csv --strategy auto --merge

# 자연어로 피벗/차트 생성 (Fallback 엔진)
python -m app.cli excel-auto --path data/sample.csv --ask "월별 카테고리 매출 피벗 만들고 막대차트"

# 파서 선택 옵션
python -m app.cli excel-auto --path data/sample.csv --ask "월별 카테고리 매출 피벗 만들고 막대차트" --parser rule    # 규칙 파서만
python -m app.cli excel-auto --path data/sample.csv --ask "월별 카테고리 매출 피벗 만들고 막대차트" --parser llm     # LLM 파서 강제

# 자연어 필터 (지역, 카테고리 등)
python -m app.cli excel-auto --path data/sample.csv --ask "월별 카테고리 매출 피벗, 지역은 서울과 부산만" --parser rule

# Excel COM 엔진 사용 (Windows + Excel 설치 시)
python -m app.cli excel-auto --path data/sample.csv --ask "월별 카테고리 매출 피벗 만들고 막대차트" --engine com

# KPI 자동 집계
python tools/eval_kpi.py

# Streamlit UI 실행
streamlit run tools/ui_app.py
```

### 3. 데모 실행

```bash
python tests/demo_run.py
```

## 📁 프로젝트 구조

```
smart_excel_copilot/
├── app/
│   ├── core/           # 핵심 기능 (프로파일링)
│   ├── excel_ops/      # 전처리 작업
│   ├── io/             # 파일 입출력
│   ├── recipes/        # 레시피 시스템
│   └── cli.py          # 명령행 인터페이스
├── data/
│   └── samples/        # 샘플 데이터
├── tests/              # 테스트 파일
└── requirements.txt    # 의존성
```

## 🔧 주요 모듈

### `app.core.profile`
- 데이터프레임 프로파일링
- 타입 추론 (숫자, 날짜, 통화, 불리언, 범주형)
- 통계 정보 생성

### `app.excel_ops.clean`
- 열명 표준화 (snake_case)
- 공백 정리
- 통화 분리 (₩, $, 원 등)
- 날짜 표준화 (YYYY-MM-DD)
- 불리언 표준화 (True/False)

### `app.excel_ops.dedupe`
- 다중 키 지원
- 보존 정책: first, last, last_by:열명
- 중복 현황 분석

### `app.excel_ops.impute`
- 결측치 처리 전략
- 자동 전략 제안
- 패턴 분석

### `app.excel_ops.outlier`
- 이상치 탐지 (IQR, Z-score)
- 처리 방법 (clip, remove, mark)
- 통계 요약

### `app.excel_ops.schema`
- 스키마 정렬 전략
- 자동 매핑
- 파일 병합

## 📊 지원 파일 형식

- **CSV**: UTF-8, UTF-8 BOM, cp949 자동 감지
- **Excel**: .xlsx, .xls

## 🎨 예시 데이터

`data/samples/transactions_utf8.csv` 파일에는 다음 시나리오가 포함되어 있습니다:
- 다양한 날짜 형식
- 통화 기호가 포함된 금액
- 중복 데이터
- 결측치
- 전각/반각 문자 혼재

## 🚧 개발 상태

- ✅ M0.5: 완전 구현
- 🔄 M1: 스켈레톤 구현 (기본 기능)
- 🔄 M2: 기본 구조 (레시피 시스템)

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해 주세요.

## 📄 라이선스

MIT License
