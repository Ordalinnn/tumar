#!/usr/bin/env bash
# Полная сборка фильма: кадры → видео → склейка с озвучкой → постер.
set -euo pipefail
cd "$(dirname "$0")/.."
FF="/c/Users/HP/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe"
FB="${FF%ffmpeg.exe}ffprobe.exe"
FRAMES="C:/Users/HP/AppData/Local/Temp/tumar-frames"
TOTAL=$(python -c "import json;print(json.load(open('video/timeline.json',encoding='utf-8'))['total'])")
FADE=$(python -c "import json;print(round(json.load(open('video/timeline.json',encoding='utf-8'))['total']-0.8,2))")

rm -rf "$FRAMES" "C:/Users/HP/AppData/Local/Temp/tumar-silent.mp4"
echo "== кадры ($TOTAL с)"
node video/render.mjs 30 "$TOTAL" "$FRAMES"
echo "== беззвучный h264"
"$FF" -y -v error -framerate 30 -start_number 0 -i "$FRAMES/%05d.jpg" \
  -vf "fade=t=in:st=0:d=0.5,fade=t=out:st=${FADE}:d=0.8,format=yuv420p" \
  -c:v libx264 -preset slow -crf 20 -profile:v high -pix_fmt yuv420p -r 30 \
  "C:/Users/HP/AppData/Local/Temp/tumar-silent.mp4"
echo "== склейка с озвучкой"
"$FF" -y -v error -i "C:/Users/HP/AppData/Local/Temp/tumar-silent.mp4" -i video/voice/narration.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -af apad -shortest \
  -movflags +faststart docs/media/tumar-radar-demo.mp4
"$FF" -v error -y -ss 3 -i docs/media/tumar-radar-demo.mp4 -frames:v 1 -q:v 3 docs/img/tumar-demo-poster.jpg
"$FB" -v error -show_entries format=duration,size:stream=codec_name,width,height,nb_frames,channels -of default=nw=1 docs/media/tumar-radar-demo.mp4
rm -rf "$FRAMES" "C:/Users/HP/AppData/Local/Temp/tumar-silent.mp4"
echo "== готово"
