#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# ── 定位 Python（避开 Microsoft Store 占位符）──────────────────
function Find-Python {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python310\python.exe')
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike '*WindowsApps*') { return $cmd.Source }
    return $null
}

$PY = Find-Python
if (-not $PY) {
    Write-Error "未找到可用的 Python（请先安装 Python 3.10+ 并加入 PATH）"
    exit 1
}
Write-Host "Python: $PY" -ForegroundColor Gray

# ── 定位 Inno Setup 的 ISCC.exe ────────────────────────────────
function Find-Iscc {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'InnoSetup6\ISCC.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    return $null
}

$ISCC = Find-Iscc
if (-not $ISCC) {
    Write-Error "Inno Setup 未找到（需要 Inno Setup 6）"
    exit 1
}
Write-Host "ISCC  : $ISCC" -ForegroundColor Gray

Write-Host "=== [1/3] 生成图标 ===" -ForegroundColor Cyan
& $PY generate_icon.py

Write-Host "=== [2/3] PyInstaller 打包 ===" -ForegroundColor Cyan
& $PY -m PyInstaller stt_local.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller 失败"; exit 1 }

Write-Host "=== [3/3] Inno Setup 生成安装包 ===" -ForegroundColor Cyan
& $ISCC installer.iss
if ($LASTEXITCODE -ne 0) { Write-Error "Inno Setup 失败"; exit 1 }

Write-Host ""
Write-Host "=== 完成 ===" -ForegroundColor Green
Write-Host "安装包位置: dist\stt_local_setup.exe" -ForegroundColor Yellow
