# VOICEVOX（ナレーションの声）

手元のMacで動く読み上げエンジン。インターネットに文を送らずに読み上げられる。HTTP（http://127.0.0.1:50021）で使う。

## 動いているか確かめる・起動する

```sh
python3 <このスキル>/scripts/voicevox.py status   # 版が出れば動いている
python3 <このスキル>/scripts/voicevox.py start    # 止まっていれば起動して、応答するまで待つ
```

エンジンの場所は、環境変数 `VOICEVOX_ENGINE_DIR` で指定する。指定がなければ `~/tools/voicevox/engine`（中に `run` がある）。最初の起動は、辞書の準備に1分ほどかかる。

## エンジンがないとき（初回だけ）

1. 空き容量を確かめる（vvpp が約2GB、展開後も約2GB）。
2. 公式のリリースから、macOS（Apple Silicon）版を取得する。
   ```sh
   V=0.26.2   # 版。新しい版は https://github.com/VOICEVOX/voicevox_engine/releases で確かめる
   mkdir -p ~/tools/voicevox && cd ~/tools/voicevox
   curl -L -C - --fail -o voicevox_engine-macos-arm64-$V.vvpp \
     https://github.com/VOICEVOX/voicevox_engine/releases/download/$V/voicevox_engine-macos-arm64-$V.vvpp
   ```
   大きいので時間がかかる。`nohup` で裏で落とし、途中で切れても `-C -` で続きから取れる。
3. GitHub の API が返す digest（sha256）と、手元の `shasum -a 256` の値が一致するかを確かめる。
4. 展開する: `unzip -q -o voicevox_engine-macos-arm64-$V.vvpp -d engine && chmod +x engine/run`
5. 起動する: `python3 <このスキル>/scripts/voicevox.py start`

動作を確かめた版は 0.26.2（macOS 13 でも動いた）。エンジンのフォルダは案件のリポジトリに含めない（大きく、案件のものでもないため）。

## 声の規約を読む

```sh
python3 <このスキル>/scripts/voicevox.py speakers        # 声の一覧（ID・名前・スタイル）
python3 <このスキル>/scripts/voicevox.py policy --id 14  # その声の利用規約
```

エンジンが返す policy が一次情報。商用・法人の利用ができるか、クレジットが要るか、事前の確認が要るかを読む。

| 声（ID） | 商用・法人 | 条件 |
|---|---|---|
| 冥鳴ひまり（14） | 可・申請不要 | クレジット「VOICEVOX:冥鳴ひまり」が必要。既定の声 |
| 九州そら、雨晴はう | 可 | クレジットが必要（詳しい規約は未読。使う前に読む） |
| No.7 | 事前の確認が必要 | No.7製作委員会への確認が取れるまで使わない |
| 青山龍星 | 事前の確認が必要 | 企業が関わる利用は事前の確認が必要 |

## 1文だけ試す

```sh
python3 <このスキル>/scripts/voicevox.py test --id 14 "ご紹介します。" --out /tmp/voice-test.wav
```

## 声のほかの選択肢
- ユーザー自身の声で録音する: 権利の心配がなく、いちばん自然。方言のある実演などは、本人の録音でないと伝わらない。
- 外部のAI音声（Googleなど）: 規約を読んでから使う。文が外部に送られる。
- macOS の読み上げ（say）: 使わない（商用の場での利用が禁じられている）。
