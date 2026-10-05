# 탁월 콘텐츠 임시저장 업로더 (Aside CLI 사용)
# 사용: upload.bat 위에 원고 폴더(repurpose)를 끌어다 놓거나, upload.bat "폴더경로"
param(
  [Parameter(Mandatory = $true)][string]$Folder,
  [string[]]$Only = @("naver", "linkedin", "threads")
)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogPath = Join-Path $Here "upload_log.json"
$Targets = [ordered]@{
  naver    = @{ File = "blog_naver.md"; Prompt = "naver.txt";    Name = "네이버 블로그" }
  linkedin = @{ File = "linkedin.md";   Prompt = "linkedin.txt"; Name = "LinkedIn" }
  threads  = @{ File = "threads.md";    Prompt = "threads.txt";  Name = "Threads" }
}

function Read-Log {
  if (Test-Path $LogPath) {
    $obj = Get-Content $LogPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $h = @{}; foreach ($p in $obj.PSObject.Properties) { $h[$p.Name] = $p.Value }; return $h
  }
  return @{}
}
function Write-Log($h) { $h | ConvertTo-Json -Depth 5 | Set-Content $LogPath -Encoding UTF8 }

if (-not (Get-Command aside -ErrorAction SilentlyContinue)) {
  Write-Host "Aside CLI를 찾을 수 없습니다. Aside 앱 > 설정에서 'CLI 설치'를 누른 뒤 창을 새로 열어 다시 실행하세요." -ForegroundColor Red
  exit 1
}
$Folder = (Resolve-Path $Folder).Path
$common = Get-Content (Join-Path (Join-Path $Here "prompts") "common.txt") -Raw -Encoding UTF8
$log = Read-Log
$work = Join-Path $Here "tasks"; New-Item -ItemType Directory -Force $work | Out-Null
$summary = @()

foreach ($key in $Targets.Keys) {
  if ($Only -notcontains $key) { continue }
  $t = $Targets[$key]
  $file = Join-Path $Folder $t.File
  if (-not (Test-Path $file)) { $summary += "$($t.Name): 원고 파일 없음 ($($t.File))"; continue }
  $hash = (Get-FileHash $file -Algorithm SHA256).Hash
  $id = "$key-$hash"
  if ($log.ContainsKey($id)) {
    $summary += "$($t.Name): 이미 임시저장함 ($($log[$id].at)) — 건너뜀"; continue
  }
  $prompt = (Get-Content (Join-Path (Join-Path $Here "prompts") $t.Prompt) -Raw -Encoding UTF8).Replace("{FILE}", $file)
  $taskFile = Join-Path $work "$key.txt"
  ($prompt + "`r`n`r`n" + $common) | Set-Content $taskFile -Encoding UTF8

  Write-Host ""
  Write-Host "▶ $($t.Name) 임시저장 시작" -ForegroundColor Cyan
  $msg = "다음 작업 지시 파일을 읽고 그대로 수행해 줘: $taskFile"
  & aside exec $msg 2>&1 | Tee-Object -Variable lines
  $text = ($lines | Out-String)
  if ($text -match "RESULT:\s*OK") {
    $log[$id] = @{ platform = $key; file = $file; at = (Get-Date -Format "yyyy-MM-dd HH:mm") }
    Write-Log $log
    $summary += "$($t.Name): 임시저장 완료"
  } else {
    $reason = if ($text -match "RESULT:\s*FAIL\s*(.*)") { $Matches[1].Trim() } else { "결과를 확인하지 못함 — Aside 앱의 작업 기록을 확인하세요" }
    $summary += "$($t.Name): 실패 — $reason"
  }
}

Write-Host ""
Write-Host "===== 결과 =====" -ForegroundColor Yellow
$summary | ForEach-Object { Write-Host $_ }
Write-Host "검수 후 각 사이트의 임시저장함에서 직접 발행하면 됩니다."
