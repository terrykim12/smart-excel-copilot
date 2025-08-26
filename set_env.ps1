# LLM 모델 환경변수 설정
Write-Host "LLM 모델 환경변수를 설정합니다..." -ForegroundColor Green

# 기본 모델 설정
$env:SEC_LLM_MODEL="qwen2.5:3b-instruct"

# 다른 모델 옵션들
Write-Host "사용 가능한 모델:" -ForegroundColor Yellow
Write-Host "  - qwen2.5:3b-instruct (기본값)" -ForegroundColor Cyan
Write-Host "  - llama3.2:3b-instruct" -ForegroundColor Cyan
Write-Host "  - mistral:7b-instruct" -ForegroundColor Cyan
Write-Host "  - codellama:7b-instruct" -ForegroundColor Cyan

Write-Host "`n현재 설정된 모델: $env:SEC_LLM_MODEL" -ForegroundColor Green
Write-Host "`n다른 모델을 사용하려면:" -ForegroundColor Yellow
Write-Host "  `$env:SEC_LLM_MODEL=`"llama3.2:3b-instruct`"" -ForegroundColor White
Write-Host "  python -m app.cli excel-auto --path data/sample.csv --ask `"요청`" --parser llm" -ForegroundColor White
