# 콘솔 한글 고정
chcp 65001 > $null
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8="1"; $env:PYTHONIOENCODING="utf-8"

Write-Host "콘솔 한글이 설정되었습니다." -ForegroundColor Green
Write-Host "이제 Python 스크립트를 실행할 수 있습니다." -ForegroundColor Yellow
