# Streamlit UI 실행 스크립트
Write-Host "🚀 Smart Excel Copilot UI 실행 중..." -ForegroundColor Green

# 환경 변수 설정
$env:PYTHONPATH = ".;smart_excel_copilot"

# Streamlit 실행
Write-Host "🌐 브라우저에서 http://localhost:8501 열기" -ForegroundColor Cyan
streamlit run tools/ui_copilot.py

