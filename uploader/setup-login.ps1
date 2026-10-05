# 처음 한 번: Aside 브라우저에서 세 사이트 로그인 (로그인은 사람이 직접)
[Console]::OutputEncoding = [Text.Encoding]::UTF8
if (-not (Get-Command aside -ErrorAction SilentlyContinue)) {
  Write-Host "Aside CLI를 찾을 수 없습니다. Aside 앱 > 설정에서 'CLI 설치'를 누른 뒤 다시 실행하세요." -ForegroundColor Red
  exit 1
}
$msg = @"
아래 세 페이지를 각각 새 탭으로 열어 두고 작업을 끝내 줘. 로그인은 사용자가 그 탭에서 직접 한다. 비밀번호를 입력하거나 추측하지 마.
- https://nid.naver.com/nidlogin.login?url=https://blog.naver.com/takwell
- https://www.linkedin.com/login
- https://www.threads.com/login
로그인할 계정: 네이버 블로그 takwell / LinkedIn lawfirm-takwell / Threads @lawfirm_takwell
"@
& aside exec $msg
Write-Host ""
Write-Host "Aside 창에 열린 세 탭에서 각각 로그인해 주세요. 로그인 상태 유지에 체크하면 다음부터는 다시 할 필요가 없습니다." -ForegroundColor Yellow
