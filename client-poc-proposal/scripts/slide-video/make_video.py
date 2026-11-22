#!/usr/bin/env python3
"""紹介動画を「説明画面＋PoCの画面写真＋字幕」で作る（スライド＋字幕方式）。

scenes.json の場面を順につなぎ、scenes.json と同じフォルダの out/ に2本を書き出す。
  - 〈name〉（声・BGM付き）.mp4 … VOICEVOX のナレーション＋BGM＋字幕。最後の場面にクレジット
  - 〈name〉（音なし）.mp4      … 字幕のみ（打ち合わせで話しながら流す用）

使い方（video/ で実行。先に VOICEVOX を起動しておく）:
  python3 make_video.py [--scenes scenes.json]
必要なもの: ffmpeg（libass付き）、uv（BGM の合成に numpy・scipy を使う）、VOICEVOX エンジン。
macOS の読み上げ音声（say、Kyoko など）は、Apple の規約で商用の場に使えないので使わない。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = "http://127.0.0.1:50021"
FPS = 30
LEAD = 0.5  # 場面が始まってから読み上げを始めるまで（秒）
TAIL = 0.6  # 読み上げが終わってから次の場面までの余白（秒）
FADE = 0.3  # 場面の切り替え（白へのフェード）の長さ（秒）


def run(*command):
    subprocess.run([str(c) for c in command], check=True, capture_output=True)


def duration_of(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def engine_running():
    try:
        with urllib.request.urlopen(f"{ENGINE}/version", timeout=3):
            return True
    except OSError:
        return False


def synthesize(text, speaker, speed, target):
    """VOICEVOX で text を読み上げ、48kHz の WAV にする。"""
    query_url = f"{ENGINE}/audio_query?" + urllib.parse.urlencode({"text": text, "speaker": speaker})
    with urllib.request.urlopen(urllib.request.Request(query_url, method="POST"), timeout=120) as response:
        query = json.loads(response.read())
    query.update(speedScale=speed, prePhonemeLength=0.05, postPhonemeLength=0.1, outputSamplingRate=48000)
    request = urllib.request.Request(f"{ENGINE}/synthesis?speaker={speaker}", data=json.dumps(query).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=300) as response:
        target.write_bytes(response.read())


def find_bgm():
    """video/ にコピーしたときは同じフォルダ、スキルのフォルダから直接使うときは一つ上を探す。"""
    for candidate in (HERE / "bgm.py", HERE.parent / "bgm.py"):
        if candidate.exists():
            return candidate
    raise SystemExit("bgm.py が見つかりません。scripts/bgm.py を make_video.py と同じフォルダにコピーしてください")


def frames(seconds):
    return max(1, round(seconds * FPS))


def ass_time(seconds):
    centis = round(seconds * 100)
    return f"{centis // 360000}:{centis // 6000 % 60:02d}:{centis // 100 % 60:02d}.{centis % 100:02d}"


def build_subtitles(scenes, target, sample_credit, voice_credit=None):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Hiragino Sans,50,&H00FFFFFF,&H00FFFFFF,&H3830211B,&H00000000,-1,0,0,0,100,100,1,0,3,20,0,2,120,120,54,1
Style: CaptionTop,Hiragino Sans,50,&H00FFFFFF,&H00FFFFFF,&H3830211B,&H00000000,-1,0,0,0,100,100,1,0,3,20,0,8,120,120,40,1
Style: Credit,Hiragino Sans,24,&H00FFFFFF,&H00FFFFFF,&H5030211B,&H00000000,0,0,0,0,100,100,0,0,3,8,0,9,40,40,24,1
Style: CreditBottom,Hiragino Sans,24,&H00FFFFFF,&H00FFFFFF,&H5030211B,&H00000000,0,0,0,0,100,100,0,0,3,8,0,1,40,40,24,1
Style: VoiceCredit,Hiragino Sans,30,&H00FFFFFF,&H00FFFFFF,&H5030211B,&H00000000,0,0,0,0,100,100,0,0,3,10,0,2,40,40,48,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if voice_credit:  # 声とBGMのクレジットは最後の場面に出す
        last = scenes[-1]
        lines.append(f"Dialogue: 1,{ass_time(last['start'] + FADE)},{ass_time(last['start'] + last['length'] - FADE)},"
                     f"VoiceCredit,,0,0,0,,{voice_credit}")
    for scene in scenes:
        start, end = scene["start"], scene["start"] + scene["length"]
        if scene.get("credit") and sample_credit:
            style = "Credit" if scene["credit"] == "top" else "CreditBottom"
            lines.append(f"Dialogue: 1,{ass_time(start + FADE)},{ass_time(end - FADE)},{style},,0,0,0,,{sample_credit}")
        captions = scene.get("captions") or []
        if not captions:
            continue
        # 読み上げの長さを、字幕の文字数に比例して分ける
        weights = [len(c.replace("\\N", "")) for c in captions]
        cursor, speech_end = start + LEAD, start + LEAD + scene["speech_length"]
        style = "CaptionTop" if scene.get("caption_top") else "Caption"
        for index, (caption, weight) in enumerate(zip(captions, weights)):
            span = scene["speech_length"] * weight / sum(weights)
            finish = speech_end + 0.3 if index == len(captions) - 1 else cursor + span
            lines.append(f"Dialogue: 0,{ass_time(cursor)},{ass_time(min(finish, end - FADE))},{style},,0,0,0,,{caption}")
            cursor += span
    target.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes", default=str(HERE / "scenes.json"))
    args = parser.parse_args()
    scenes_path = Path(args.scenes).resolve()
    config = json.loads(scenes_path.read_text(encoding="utf-8"))
    base = scenes_path.parent
    assets = base / config.get("assets", "assets")
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)
    speaker, speed = config.get("speaker", 14), config.get("speed", 1.05)
    use_bgm = config.get("bgm", True)
    voice_credit = f"ナレーション：VOICEVOX:{config.get('speaker_name', '冥鳴ひまり')}"
    if use_bgm:
        voice_credit += " ｜ BGM：オリジナル（Not a Square 制作）"
    name = config["name"]
    output_voiced = out_dir / f"{name}（{'声・BGM付き' if use_bgm else '声付き'}）.mp4"
    output_silent = out_dir / f"{name}（音なし）.mp4"

    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg（libass付き）が必要です")
    if not engine_running():
        raise SystemExit(f"VOICEVOX エンジンが {ENGINE} で動いていません。起動してから実行してください")
    if use_bgm and not shutil.which("uv"):
        raise SystemExit("BGM の合成に uv が必要です（bgm を false にすれば BGM なしで作れます）")

    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        timeline, start = [], 0.0
        for number, scene in enumerate(config["scenes"], 1):
            scene = dict(scene)
            if scene.get("speech"):
                raw = work / f"speech{number:02d}-raw.wav"
                synthesize(scene["speech"], speaker, speed, raw)
                scene["speech_file"] = work / f"speech{number:02d}.wav"
                run("ffmpeg", "-y", "-i", raw, "-ar", "48000", "-ac", "1", scene["speech_file"])
                scene["speech_length"] = duration_of(scene["speech_file"])
                length = LEAD + scene["speech_length"] + TAIL
            else:
                scene["speech_length"] = 0.0
                length = scene.get("duration", 3.0)
            if scene.get("sequence"):
                length = max(length, 0.8 + scene["frames"] / scene["sequence_fps"] + 1.2)
            scene["length"] = frames(length) / FPS
            scene["start"] = start
            start += scene["length"]
            timeline.append(scene)

        clips, sounds = [], []
        for number, scene in enumerate(timeline, 1):
            length = scene["length"]
            fade = f"fade=t=in:st=0:d={FADE}:color=white,fade=t=out:st={length - FADE:.3f}:d={FADE}:color=white"
            scale = "scale=1920:1080:flags=lanczos,setsar=1"
            clip = work / f"clip{number:02d}.mp4"
            if scene.get("sequence"):  # 連番の静止画を動かしてから、最後の1枚で止める
                hold = length - 0.8 - scene["frames"] / scene["sequence_fps"]
                video_filter = (f"fps={FPS},{scale},tpad=start_duration=0.8:start_mode=clone:"
                                f"stop_duration={hold:.3f}:stop_mode=clone,{fade},format=yuv420p")
                inputs = ["-framerate", str(scene["sequence_fps"]), "-i", assets / scene["sequence"]]
            else:
                video_filter = f"{scale},{fade},format=yuv420p"
                inputs = ["-loop", "1", "-framerate", str(FPS), "-i", assets / scene["image"]]
            run("ffmpeg", "-y", *inputs, "-vf", video_filter, "-frames:v", frames(length), "-r", FPS,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", clip)
            clips.append(clip)
            sound = work / f"sound{number:02d}.wav"
            if scene.get("speech_file"):
                delay = int(LEAD * 1000)
                run("ffmpeg", "-y", "-i", scene["speech_file"], "-af", f"adelay={delay},apad=whole_dur={length:.3f}",
                    "-t", f"{length:.3f}", "-ar", "48000", "-ac", "1", sound)
            else:
                run("ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{length:.3f}", sound)
            sounds.append(sound)

        for list_name, items in (("clips.txt", clips), ("sounds.txt", sounds)):
            (work / list_name).write_text("".join(f"file '{item}'\n" for item in items), encoding="utf-8")
        joined_video, joined_sound = work / "video.mp4", work / "voice.wav"
        run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", work / "clips.txt", "-c", "copy", joined_video)
        run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", work / "sounds.txt", "-c", "copy", joined_sound)

        # 音: ナレーションの音量をそろえ、BGM を合成して混ぜる（声が出ている間は BGM を下げる）
        audio = work / "audio.m4a"
        voice_chain = "aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo"
        if use_bgm:
            bgm = work / "bgm.wav"
            run("uv", "run", "--quiet", "--with", "numpy", "--with", "scipy", "python", find_bgm(),
                "--duration", f"{start:.3f}", "--out", bgm)
            run("ffmpeg", "-y", "-i", joined_sound, "-i", bgm, "-filter_complex",
                f"[0:a]{voice_chain},asplit=2[voice][sc];"
                "[1:a]aresample=48000,loudnorm=I=-27:TP=-3:LRA=11,aresample=48000[bgm];"
                "[bgm][sc]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=700[duck];"
                "[voice][duck]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]",
                "-map", "[out]", "-t", f"{start:.3f}", "-c:a", "aac", "-b:a", "160k", audio)
        else:
            run("ffmpeg", "-y", "-i", joined_sound, "-af", voice_chain, "-c:a", "aac", "-b:a", "160k", audio)

        subtitles, subtitles_voiced = work / "captions.ass", work / "captions-voiced.ass"
        sample_credit = config.get("sample_credit", "")
        build_subtitles(timeline, subtitles, sample_credit)
        build_subtitles(timeline, subtitles_voiced, sample_credit, voice_credit=voice_credit)
        run("ffmpeg", "-y", "-i", joined_video, "-i", audio, "-vf", f"ass={subtitles_voiced}",
            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-movflags", "+faststart", "-shortest", output_voiced)
        run("ffmpeg", "-y", "-i", joined_video, "-vf", f"ass={subtitles}", "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", output_silent)
        summary = [{"scene": n, "start": round(s["start"], 2), "length": round(s["length"], 2),
                    "image": s.get("image") or s.get("sequence")} for n, s in enumerate(timeline, 1)]
        print(json.dumps({"total_seconds": round(start, 2), "outputs": [str(output_voiced), str(output_silent)],
                          "scenes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
