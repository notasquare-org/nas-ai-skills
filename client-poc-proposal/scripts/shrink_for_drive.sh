#!/bin/sh
# Driveコネクタの上限（1ファイル10MB）に収まるよう、動画を縮める。見た目はほぼ変わらない。
#   sh shrink_for_drive.sh <動画.mp4> [上限MB（既定 9.5）]   → 同じフォルダに <動画>-drive.mp4
# 画質の設定（CRF）を 24 から順に上げ、上限に収まった所で止める。元のファイルは変えない。
set -eu
if [ $# -lt 1 ]; then
  echo "使い方: sh shrink_for_drive.sh <動画.mp4> [上限MB]"
  exit 1
fi
in="$1"
limit_mb="${2:-9.5}"
[ -f "$in" ] || { echo "ファイルがありません: $in"; exit 1; }
out="${in%.*}-drive.mp4"
limit=$(awk -v m="$limit_mb" 'BEGIN { printf "%d", m * 1000 * 1000 }')
size=$(stat -f%z "$in")
if [ "$size" -le "$limit" ]; then
  cp "$in" "$out"
  echo "縮めなくても収まります: $out（$size バイト）"
  exit 0
fi
for crf in 24 26 28 30 32; do
  ffmpeg -nostdin -y -loglevel error -i "$in" -map 0 -c:v libx264 -crf "$crf" -preset slow -pix_fmt yuv420p \
    -c:a aac -b:a 128k -movflags +faststart "$out"
  size=$(stat -f%z "$out")
  if [ "$size" -le "$limit" ]; then
    echo "CRF $crf で収まりました: $out（$size バイト）"
    exit 0
  fi
done
echo "CRF 32 でも上限を超えました: $out（$size バイト）。解像度を下げるか、分けて入れることを検討してください。"
exit 1
