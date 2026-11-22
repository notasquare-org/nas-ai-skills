#!/usr/bin/env python3
"""VOICEVOX エンジンの確認・起動と、声の規約の表示（紹介動画のナレーション用）。

  python3 voicevox.py status                  動いているか（版を表示）
  python3 voicevox.py start                   止まっていれば起動して、応答するまで待つ
  python3 voicevox.py speakers                声の一覧（名前・スタイル・ID）
  python3 voicevox.py policy --id 14          その声の利用規約（エンジンが返す policy。一次情報）
  python3 voicevox.py test --id 14 "文" --out /tmp/voice-test.wav   1文だけ読み上げて確かめる

エンジンの場所: 環境変数 VOICEVOX_ENGINE_DIR。なければ ~/tools/voicevox/engine（中に run がある）。
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path

ENGINE = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
ENGINE_DIR = Path(os.environ.get("VOICEVOX_ENGINE_DIR", str(Path.home() / "tools" / "voicevox" / "engine"))).expanduser()


def get(path, timeout=30):
    with urllib.request.urlopen(f"{ENGINE}{path}", timeout=timeout) as response:
        return json.loads(response.read())


def version():
    try:
        return get("/version", timeout=3)
    except OSError:
        return None


def require_engine():
    if not version():
        raise SystemExit(f"VOICEVOX エンジンが動いていません（{ENGINE}）。先に start を実行してください。")


def cmd_status(_):
    found = version()
    if found:
        print(f"動いています: VOICEVOX エンジン {found}（{ENGINE}）")
        return 0
    print(f"動いていません（{ENGINE}）。起動するには: python3 {Path(__file__).name} start")
    return 1


def cmd_start(_):
    if version():
        print(f"すでに動いています: VOICEVOX エンジン {version()}")
        return 0
    run = ENGINE_DIR / "run"
    if not run.exists():
        print(f"エンジンが見つかりません: {run}\n"
              "references/voicevox.md の「エンジンがないとき」の手順で取得してください。"
              "別の場所にあるなら、環境変数 VOICEVOX_ENGINE_DIR でそのフォルダを指定します。")
        return 1
    log = ENGINE_DIR.parent / "engine.log"
    port = ENGINE.rsplit(":", 1)[-1]
    with open(log, "ab") as out:
        subprocess.Popen([str(run), "--host", "127.0.0.1", "--port", port], cwd=str(ENGINE_DIR),
                         stdout=out, stderr=out, start_new_session=True)
    for _ in range(90):  # 初回は辞書の準備で1分ほどかかる
        time.sleep(2)
        if version():
            print(f"起動しました: VOICEVOX エンジン {version()}（ログ: {log}）")
            return 0
    print(f"起動を確かめられませんでした。ログを見てください: {log}")
    return 1


def speakers():
    require_engine()
    return get("/speakers")


def cmd_speakers(_):
    for speaker in speakers():
        styles = "、".join(f"{style['name']}={style['id']}" for style in speaker["styles"])
        print(f"{speaker['name']}: {styles}")
    return 0


def cmd_policy(args):
    for speaker in speakers():
        for style in speaker["styles"]:
            if style["id"] == args.id:
                query = urllib.parse.urlencode({"speaker_uuid": speaker["speaker_uuid"]})
                policy = get(f"/speaker_info?{query}").get("policy") or "（policy が空です）"
                print(f"# {speaker['name']}（{style['name']}、ID {args.id}）の利用規約\n")
                print(policy)
                return 0
    print(f"ID {args.id} の声が見つかりません。speakers で一覧を見てください。")
    return 1


def synthesize(text, speaker, target, speed=1.05):
    """text を読み上げて 48kHz の WAV にし、秒数を返す。"""
    query_url = f"{ENGINE}/audio_query?" + urllib.parse.urlencode({"text": text, "speaker": speaker})
    with urllib.request.urlopen(urllib.request.Request(query_url, method="POST"), timeout=120) as response:
        query = json.loads(response.read())
    query.update(speedScale=speed, prePhonemeLength=0.05, postPhonemeLength=0.1, outputSamplingRate=48000)
    request = urllib.request.Request(f"{ENGINE}/synthesis?speaker={speaker}", data=json.dumps(query).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=300) as response:
        Path(target).write_bytes(response.read())
    with wave.open(str(target)) as wav:
        return wav.getnframes() / wav.getframerate()


def cmd_test(args):
    require_engine()
    seconds = synthesize(args.text, args.id, args.out, args.speed)
    print(f"保存しました: {args.out}（{seconds:.2f}秒）")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="動いているか").set_defaults(func=cmd_status)
    sub.add_parser("start", help="起動して待つ").set_defaults(func=cmd_start)
    sub.add_parser("speakers", help="声の一覧").set_defaults(func=cmd_speakers)
    policy = sub.add_parser("policy", help="声の利用規約")
    policy.add_argument("--id", type=int, default=14)
    policy.set_defaults(func=cmd_policy)
    test = sub.add_parser("test", help="1文だけ読み上げる")
    test.add_argument("text")
    test.add_argument("--id", type=int, default=14)
    test.add_argument("--speed", type=float, default=1.05)
    test.add_argument("--out", default="/tmp/voice-test.wav")
    test.set_defaults(func=cmd_test)
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
