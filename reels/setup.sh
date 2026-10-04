#!/usr/bin/env bash
# 의존성 설치 + 한글 폰트(Pretendard, OFL) 내려받기
set -euo pipefail
cd "$(dirname "$0")"
pip install -r requirements.txt
mkdir -p fonts
if ! ls fonts/*.otf >/dev/null 2>&1; then
  tmp=$(mktemp -d)
  (cd "$tmp" && npm pack pretendard@1.3.9 --silent >/dev/null && tar xzf pretendard-*.tgz)
  cp "$tmp"/package/dist/public/static/Pretendard-{Bold,ExtraBold,Black}.otf fonts/
  rm -rf "$tmp"
fi
command -v ffmpeg >/dev/null || echo "ffmpeg(libass 포함)을 설치하세요: brew install ffmpeg / apt install ffmpeg"
echo "준비 완료"
