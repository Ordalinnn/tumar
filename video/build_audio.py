"""Озвучка фильма: синтез локальным голосом Windows, замер длительностей,
перетайминг сцен в film.html и сборка команды микса.

Запуск: python video/build_audio.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

VIDEO = Path(__file__).resolve().parent
FILM = VIDEO / "film.html"
CUES = VIDEO / "cues.json"
VOICE = VIDEO / "voice"
FFMPEG = r"C:/Users/HP/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin/ffmpeg.exe"
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

LEAD = 0.6      # первая фраза после начала сцены
BETWEEN = 0.45  # пауза между фразами внутри сцены
TAIL = 1.3      # воздух после последней фразы сцены
GAP = 0.12      # чёрный стык между сценами


def synth(lines: list[str]) -> list[Path]:
    VOICE.mkdir(parents=True, exist_ok=True)
    txt = VOICE / "lines.txt"
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(VIDEO / "tts_onecore.ps1"),
         "-TextFile", str(txt), "-OutDir", str(VOICE), "-Match", "Pavel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if out.returncode != 0:
        print(out.stdout, out.stderr)
        raise SystemExit("синтез не удался")
    files = sorted(VOICE.glob("oc*.wav"))
    if len(files) != len(lines):
        raise SystemExit(f"ждали {len(lines)} дорожек, получили {len(files)}")
    return files


def duration(path: Path) -> float:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def main() -> None:
    cues = json.loads(CUES.read_text(encoding="utf-8"))
    files = synth([c["text"] for c in cues])
    for cue, path in zip(cues, files):
        cue["wav"] = path.name
        cue["dur"] = round(duration(path), 3)

    scenes: dict[str, list[dict]] = {}
    for cue in cues:
        scenes.setdefault(cue["scene"], []).append(cue)

    order = [f"s{i}" for i in range(1, 9)]
    clock = 0.0
    plan = []
    for sid in order:
        start = 0.4 if sid == "s1" else round(clock + GAP, 3)
        local = LEAD
        for cue in scenes[sid]:
            cue["at"] = round(start + local, 3)
            local += cue["dur"] + BETWEEN
        length = round(local - BETWEEN + TAIL, 3)
        plan.append({"id": sid, "in": start, "out": round(start + length, 3), "cues": scenes[sid]})
        clock = start + length

    total = round(clock + 0.2, 3)

    # --- перетайминг film.html -------------------------------------------------
    html = FILM.read_text(encoding="utf-8")

    def sub(pattern: str, repl: str, count: int = 1) -> None:
        nonlocal html
        html, n = re.subn(pattern, repl, html, count=count)
        if n != count:
            raise SystemExit(f"не нашёл в film.html: {pattern}")

    for scene in plan:
        sub(
            rf'(<section id="{scene["id"]}"[^>]*?)data-in="[0-9.]+" data-out="[0-9.]+"',
            rf'\g<1>data-in="{scene["in"]:.2f}" data-out="{scene["out"]:.2f}"',
        )

    s2 = scenes["s2"]
    s4 = scenes["s4"]
    s5 = scenes["s5"]

    def loc(cue: dict) -> float:
        start = next(s["in"] for s in plan if s["id"] == cue["scene"])
        return round(cue["at"] - start, 2)

    def tag(pattern: str, build: str) -> None:
        nonlocal html
        hits = len(re.findall(pattern, html))
        if hits != 1:
            raise SystemExit(f'ожидал один тег для {pattern}, нашёл {hits}')
        html = re.sub(pattern, lambda _: build, html, count=1)

    t2a_out = loc(s2[1]) - 0.25
    t2b_in = loc(s2[1]) - 0.65
    t4a_out = loc(s4[1]) - 0.05
    t4b_in = loc(s4[1]) - 0.65
    t4b_out = loc(s4[2]) - 0.05
    t4c_in = loc(s4[2]) - 0.65
    g1, g2, g3 = (loc(c) for c in s5)

    tag(r'<div data-t="0\.1" data-o="[0-9.]+">',
        f'<div data-t="0.1" data-o="{t2a_out:.2f}">')
    tag(r'justify-content:center" data-t="[0-9.]+" data-an="rise">',
        f'justify-content:center" data-t="{t2b_in:.2f}" data-an="rise">')

    tag(r'<div class="shot" data-t="0\.2" data-o="[0-9.]+"><img src="\.\./docs/img/app-client\.jpg"',
        f'<div class="shot" data-t="0.2" data-o="{t4a_out:.2f}"><img src="../docs/img/app-client.jpg"')
    tag(r'<div class="shot" data-t="[0-9.]+" data-o="[0-9.]+"><img src="\.\./docs/img/app-analyst\.jpg"',
        f'<div class="shot" data-t="{t4b_in:.2f}" data-o="{t4b_out:.2f}"><img src="../docs/img/app-analyst.jpg"')
    tag(r'<div class="shot" data-t="[0-9.]+"><img src="\.\./docs/img/app-quality\.jpg"',
        f'<div class="shot" data-t="{t4c_in:.2f}"><img src="../docs/img/app-quality.jpg"')

    tag(r'<div class="cap" data-t="0\.15" data-o="[0-9.]+"><b>Клиент</b>',
        f'<div class="cap" data-t="0.15" data-o="{t4a_out:.2f}"><b>Клиент</b>')
    tag(r'<div class="cap" data-t="[0-9.]+" data-o="[0-9.]+"><b>Аналитик</b>',
        f'<div class="cap" data-t="{t4b_in:.2f}" data-o="{t4b_out:.2f}"><b>Аналитик</b>')
    tag(r'<div class="cap" data-t="[0-9.]+"><b>Качество</b>',
        f'<div class="cap" data-t="{t4c_in:.2f}"><b>Качество</b>')

    tag(r'<div class="test fail" data-t="0\.9" data-an="rise" data-ga="[0-9.]+" data-go="[0-9.]+">',
        f'<div class="test fail" data-t="0.9" data-an="rise" data-ga="{g1 - 0.1:.2f}" data-go="{g2 - 0.2:.2f}">')
    tag(r'<div class="test warn" data-t="1\.3" data-an="rise" data-ga="[0-9.]+" data-go="[0-9.]+">',
        f'<div class="test warn" data-t="1.3" data-an="rise" data-ga="{g2 - 0.1:.2f}" data-go="{g3 - 0.2:.2f}">')
    tag(r'<div class="test t3" data-t="1\.7" data-an="rise" data-ga="[0-9.]+"',
        f'<div class="test t3" data-t="1.7" data-an="rise" data-ga="{g3 - 0.1:.2f}"')

    sub(r"const TOTAL = [0-9.]+;", f"const TOTAL = {total:.2f};")
    FILM.write_text(html, encoding="utf-8")

    # --- команды ffmpeg -------------------------------------------------------
    voice_chain = (
        "aresample=48000,highpass=f=85,lowpass=f=12500,"
        "equalizer=f=240:t=q:w=1:g=-2,equalizer=f=3300:t=q:w=1.4:g=2.5,"
        "acompressor=threshold=-18dB:ratio=3:attack=8:release=200:makeup=6dB"
    )
    inputs = " ".join(f'-i "{VIDEO / "voice" / c["wav"]}"' for c in cues)
    chains = []
    for i, cue in enumerate(cues):
        ms = int(round(cue["at"] * 1000))
        chains.append(f"[{i}:a]{voice_chain},adelay={ms}|{ms}[a{i}]")
    mix_inputs = "".join(f"[a{i}]" for i in range(len(cues)))
    graph = (
        ";".join(chains)
        + f";{mix_inputs}amix=inputs={len(cues)}:normalize=0[raw]"
        + f";[raw]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={total - 0.9:.2f}:d=0.9[aout]"
    )

    (VIDEO / "mix.sh").write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        f'FF="{FFMPEG}"\n'
        f'"$FF" -y -v error {inputs} -filter_complex "{graph}" -map "[aout]" -ac 2 -ar 48000 '
        f'-c:a pcm_s16le "{VIDEO / "voice" / "narration.wav"}"\n',
        encoding="utf-8",
    )

    (VIDEO / "timeline.json").write_text(
        json.dumps({"total": total, "scenes": plan}, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"сцен: {len(plan)}, фраз: {len(cues)}, всего: {total:.1f} с")
    for scene in plan:
        print(f'  {scene["id"]}: {scene["in"]:6.2f} -> {scene["out"]:6.2f}  ({len(scene["cues"])} фраз)')
    print(f'фейд видео: st={total - 0.8:.2f}')


if __name__ == "__main__":
    main()
