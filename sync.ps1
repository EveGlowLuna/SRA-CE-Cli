# sync.ps1 - PowerShell包装器
param(
    [switch]$Help,
    [switch]$DryRun,
    [string]$Action = ""
)

if ($Help) {
    Write-Host "🔄 上游同步工具" -ForegroundColor Cyan
    Write-Host "用法:" -ForegroundColor White
    Write-Host "  .\sync.ps1                  # 交互模式" -ForegroundColor Gray
    Write-Host "  .\sync.ps1 -DryRun         # 只预览" -ForegroundColor Gray
    Write-Host "  .\sync.ps1 -Action status  # 快速状态" -ForegroundColor Gray
    exit 0
}

# 检查Python
$python = "python"
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $python = "python3"
}

if (!(Get-Command $python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    exit 1
}

# 运行Python脚本
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyScript = Join-Path $scriptDir "sync_upstream.py"

if ($DryRun) {
    & $python $pyScript --dry-run
} elseif ($Action) {
    & $python $pyScript --action $Action
} else {
    & $python $pyScript
}

# 显示后续步骤
Write-Host "`n📝 后续步骤:" -ForegroundColor Yellow
Write-Host "  1. 解决冲突 (如果有)" -ForegroundColor White
Write-Host "  2. 提交更改: git commit -m 'sync: 上游更新'" -ForegroundColor White
Write-Host "  3. 推送: git push origin main" -ForegroundColor White
Write-Host "  4. 在主仓库更新子模块引用" -ForegroundColor White