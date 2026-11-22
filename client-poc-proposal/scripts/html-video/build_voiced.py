"""紹介動画の「声・BGM付き」版を作る（VOICEVOX のナレーション＋ bgm.py で合成した BGM）。

1. narration.json の各文を VOICEVOX エンジン（127.0.0.1:50021）で読み上げて WAV にする
2. 声の長さに合わせて場面の止め時間を計算し、out/timing.json に書く
3. BGM を合成し、ナレーションと混ぜる（声が出ている間は BGM を下げる）
4. render.mjs で映像を書き出し、音と合わせる

使い方（video/ で実行。先に VOICEVOX を起動しておく）:
  uv run --with numpy --with scipy python build_voiced.py --speaker 14 --name 冥鳴ひまり
  --no-bgm で BGM なし、--skip-video で音だけ作る。出力は --out（既定 out/video-voice.mp4）。

narration.json の形:
  {"duration": 動画の秒数（video.html の DURATION と同じ）,
   "lines": [{"id": "n01", "at": 話し始める場面の秒, "hold": その場面の表示が出そろう秒, "text": "読み上げる文"}, ...]}
声が場面より長いときは、hold の所で映像を止めて待つ（アニメの速さは変えない）。
"""

import argparse
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = "http://127.0.0.1:50021"
LEAD, TAIL = 0.25, 0.65  # 場面が始まってから声が出るまで / 声が終わってから次の場面まで（秒）


def synth(text: str, speaker: int, speed: float, path: Path) -> float:
    q = urllib.parse.urlencode({"text": text, "speaker": speaker})
    with urllib.request.urlopen(urllib.request.Request(f"{ENGINE}/audio_query?{q}", method="POST"), timeout=120) as r:
        query = json.loads(r.read())
    query.update(speedScale=speed, prePhonemeLength=0.05, postPhonemeLength=0.1, outputSamplingRate=48000)
    req = urllib.request.Request(f"{ENGINE}/synthesis?speaker={speaker}", data=json.dumps(query).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        path.write_bytes(r.read())
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def run(cmd: list) -> None:
    subprocess.run([str(c) for c in cmd], check=True)


def find(name: str) -> Path:
    """video/ にコピーしたときは同じフォルダ、スキルのフォルダから直接使うときは一つ上を探す。"""
    for candidate in (HERE / name, HERE.parent / name):
        if candidate.exists():
            return candidate
    raise SystemExit(f"{name} が見つかりません。scripts/{name} を build_voiced.py と同じフォルダにコピーしてください")


def load_narration(path: Path, duration):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        if duration is None:
            raise SystemExit("narration.json が配列のときは、--duration で動画の秒数を指定してください")
        return float(duration), data
    return float(duration or data["duration"]), data["lines"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speaker", type=int, default=14, help="VOICEVOX のスタイルID（冥鳴ひまり=14）")
    ap.add_argument("--name", default="冥鳴ひまり", help="クレジットに出す声の名前")
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--narration", default=str(HERE / "narration.json"))
    ap.add_argument("--html", default=str(HERE / "video.html"))
    ap.add_argument("--duration", type=float, help="narration.json に duration がないときの動画の秒数")
    ap.add_argument("--out", default=str(HERE / "out" / "video-voice.mp4"))
    ap.add_argument("--no-bgm", action="store_true")
    ap.add_argument("--skip-video", action="store_true")
    args = ap.parse_args()

    try:
        urllib.request.urlopen(f"{ENGINE}/version", timeout=3).close()
    except OSError:
        raise SystemExit(f"VOICEVOX エンジンが {ENGINE} で動いていません。起動してから実行してください")

    out_dir = Path(args.html).resolve().parent / "out"
    narr_dir = out_dir / "narration"
    narr_dir.mkdir(parents=True, exist_ok=True)
    duration, segs = load_narration(Path(args.narration), args.duration)

    # 1. 読み上げ
    for s in segs:
        s["file"] = str(narr_dir / f"{s['id']}.wav")
        s["dur"] = round(synth(s["text"], args.speaker, args.speed, Path(s["file"])), 3)
        print(f"{s['id']} {s['dur']:5.2f}s {s['text']}")

    # 2. 場面の止め時間
    t = segs[0]["at"]
    for i, s in enumerate(segs):
        s["next"] = segs[i + 1]["at"] if i + 1 < len(segs) else duration
        if not s["at"] <= s["hold"] < s["next"]:
            raise SystemExit(f"{s['id']}: hold は at 以上、次の文の at より前にしてください")
        length = s["next"] - s["at"]
        s["newLen"] = round(max(length, LEAD + s["dur"] + TAIL), 3)
        s["newStart"] = round(t, 3)
        s["clipStart"] = round(t + LEAD, 3)
        t += s["newLen"]
    total = round(t, 3)
    timing_path = out_dir / "timing.json"
    timing_path.write_text(json.dumps({"total": total, "segments": segs}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"total: {total:.1f}s（元は {duration}s）")

    # 3. 音: ナレーションを並べて音量をそろえ、BGM を合成して混ぜる
    inputs, filters = [], []
    for i, s in enumerate(segs):
        inputs += ["-i", s["file"]]
        ms = int(s["clipStart"] * 1000)
        filters.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(segs)))
    filters.append(f"{mix}amix=inputs={len(segs)}:normalize=0,apad=whole_dur={total},atrim=0:{total},"
                   f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[out]")
    narration = out_dir / "narration.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[out]", "-ac", "1", narration])
    audio = out_dir / "audio.m4a"
    if args.no_bgm:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", narration, "-ac", "2", "-c:a", "aac", "-b:a", "160k", audio])
    else:
        bgm = out_dir / "bgm.wav"
        run([sys.executable, find("bgm.py"), "--duration", total, "--out", bgm])
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", narration, "-i", bgm, "-filter_complex",
             "[1:a]aresample=48000,loudnorm=I=-27:TP=-3:LRA=11,aresample=48000[bgm];"
             "[0:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[voice][sc];"
             "[bgm][sc]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=700[duck];"
             "[voice][duck]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]",
             "-map", "[out]", "-c:a", "aac", "-b:a", "160k", audio])

    # 4. 映像を書き出して、音と合わせる
    if args.skip_video:
        return
    credit = f"ナレーション：VOICEVOX:{args.name}"
    if not args.no_bgm:
        credit += " ｜ BGM：オリジナル（Not a Square 制作）"
    video = out_dir / "video-voice-video.mp4"
    run(["node", find("render.mjs"), "--html", Path(args.html).resolve(), "--timing", timing_path,
         "--out", video, "--credit", credit])
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", out])
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
