#!/usr/bin/env bash
# ============================================================
# package_class_files.sh
# CLASS_FILES 폴더를 패들렛 업로드용 CLASS_FILES.zip 으로 묶습니다.
# 사용법: 이 파일이 있는 폴더에서  bash package_class_files.sh
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/CLASS_FILES"
OUT="$ROOT/CLASS_FILES.zip"

if [ ! -d "$SRC" ]; then
  echo "오류: CLASS_FILES 폴더가 없습니다: $SRC" >&2
  exit 1
fi

echo "== 배포 전 필수 파일 점검 =="
MISSING=0
check() { if [ -e "$1" ]; then echo "  [OK]   $2"; else echo "  [없음] $2"; MISSING=1; fi; }

check "$SRC/02_PHOTOSHOP/banner_template.psd"       "02_PHOTOSHOP/banner_template.psd"
check "$SRC/03_AFTER_EFFECTS/broadcast_template.aep" "03_AFTER_EFFECTS/broadcast_template.aep"
# 01_INPUT 상품 이미지 1장 이상?
if ls "$SRC/01_INPUT"/product_*.png >/dev/null 2>&1; then
  echo "  [OK]   01_INPUT/product_*.png ( $(ls "$SRC/01_INPUT"/product_*.png | wc -l | tr -d ' ') 장 )"
else
  echo "  [없음] 01_INPUT/product_*.png (상품 이미지)"; MISSING=1
fi
check "$SRC/04_SCRIPT/규격변환.jsx"     "04_SCRIPT/규격변환.jsx"
check "$SRC/04_SCRIPT/배너채우기.jsx"   "04_SCRIPT/배너채우기.jsx"
check "$SRC/04_SCRIPT/영상채우기.jsx"   "04_SCRIPT/영상채우기.jsx"
check "$SRC/04_SCRIPT/config.json"      "04_SCRIPT/config.json"

if [ "$MISSING" -ne 0 ]; then
  echo ""
  echo "⚠️  [없음] 항목이 있습니다. 각 폴더의 '_..._제작안내' 문서를 참고해 채운 뒤 다시 실행하세요."
  echo "    (스크립트/워크시트만 먼저 묶고 싶으면 아래 --force 로 강제 압축)"
  if [ "${1:-}" != "--force" ]; then exit 2; fi
  echo "→ --force 지정: 미완성 상태로 압축을 진행합니다."
fi

echo ""
echo "== 압축 중 =="
rm -f "$OUT"
# 안내용 밑줄 파일(_로 시작)과 제작안내 문서는 제외하고 묶고 싶다면 아래 -x 주석 해제
( cd "$ROOT" && zip -r -X "$OUT" CLASS_FILES \
    -x "CLASS_FILES/**/.DS_Store" \
    >/dev/null )
echo "완료: $OUT"
du -h "$OUT" | awk '{print "크기: "$1}'
