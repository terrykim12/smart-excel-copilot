chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8="1"; $env:PYTHONIOENCODING="utf-8"

Write-Host "🚀 Smart Excel Copilot 설치 시작..." -ForegroundColor Green

# 가상환경 생성
if (!(Test-Path ".venv")) {
    Write-Host "📦 가상환경 생성 중..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "✅ 가상환경 이미 존재" -ForegroundColor Green
}

# 가상환경 활성화
Write-Host "🔧 가상환경 활성화 중..." -ForegroundColor Yellow
. .\.venv\Scripts\Activate.ps1

# 의존성 설치
Write-Host "📚 패키지 설치 중..." -ForegroundColor Yellow
pip install -r requirements.txt

# 개발 모드 설치 (편집 가능)
Write-Host "🔧 개발 모드 설치 중..." -ForegroundColor Yellow
pip install -e .

# pipx로 전역 설치 (선택사항)
Write-Host "🌐 pipx 전역 설치 중..." -ForegroundColor Yellow
pip install pipx
pipx install -e .

Write-Host "✅ 설치 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "🧪 테스트 명령어:" -ForegroundColor Cyan
Write-Host "1) 프로파일링: python -m app.cli profile --path data/goldensets/s01_mixed_currency.csv" -ForegroundColor White
Write-Host "2) 전처리: python -m app.cli preprocess --path data/goldensets/s01_mixed_currency.csv --apply" -ForegroundColor White
Write-Host "3) 성능테스트: python tests/bench_run.py --rows 120000" -ForegroundColor White
