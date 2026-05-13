#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$ISCC = "$env:LOCALAPPDATA\InnoSetup6\ISCC.exe"
if (-not (Test-Path $ISCC)) {
    Write-Error "Inno Setup 未找到: $ISCC"
    exit 1
}

Write-Host "=== [1/3] 生成图标 ===" -ForegroundColor Cyan
python generate_icon.py

Write-Host "=== [2/3] PyInstaller 打包 ===" -ForegroundColor Cyan
python -m PyInstaller stt_local.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller 失败"; exit 1 }

Write-Host "=== [3/3] Inno Setup 生成安装包 ===" -ForegroundColor Cyan
& $ISCC installer.iss
if ($LASTEXITCODE -ne 0) { Write-Error "Inno Setup 失败"; exit 1 }

Write-Host ""
Write-Host "=== 完成 ===" -ForegroundColor Green
Write-Host "安装包位置: dist\stt_local_setup.exe" -ForegroundColor Yellow
