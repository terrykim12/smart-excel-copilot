# Ollama 설치 및 설정
Write-Host "Ollama 설치를 시작합니다..." -ForegroundColor Green

# 1. Ollama 설치
Write-Host "1. Ollama 설치 중..." -ForegroundColor Yellow
winget install Ollama.Ollama

# 2. Ollama 서비스 시작
Write-Host "2. Ollama 서비스 시작 중..." -ForegroundColor Yellow
Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden

# 3. 모델 다운로드
Write-Host "3. qwen2.5:3b-instruct 모델 다운로드 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 5  # 서비스 시작 대기
ollama pull qwen2.5:3b-instruct

Write-Host "설치가 완료되었습니다!" -ForegroundColor Green
Write-Host "이제 자연어 파서를 사용할 수 있습니다." -ForegroundColor Yellow
