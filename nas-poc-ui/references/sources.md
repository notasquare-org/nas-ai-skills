# 公式資料と判断への使い方

参照確認日：2026-10-28。

レイアウトを考える原則とWebでの操作性を参照する。AppleやAndroidのネイティブ部品、固定位置、寸法、実装APIをそのままWebに要求するものではない。P1〜P8、配置のトレードオフ、用途別の例は、これらの原則を基にしたNaS向けの整理である。

## layout

- [Apple HIG — Layout](https://developer.apple.com/design/human-interface-guidelines/layout)：情報の階層、関連する内容のまとまり、画面サイズの変化に対応する考え方。アプリ名だけで構成を固定せず、内容と作業の優先度から決める際の参考にする。

## basic-layouts

- [Apple HIG — Split views](https://developer.apple.com/design/human-interface-guidelines/split-views)：一覧から選んだ内容を隣で見る構造、現在の選択の明示、複数ペインに必要な幅を考える参考。
- [Material 3 — Canonical layouts](https://m3.material.io/foundations/layout/canonical-examples/overview)：feed、list-detail、supporting paneという基本構造。主に情報の関係を読むために使う。
- [Android Developers — Canonical layouts](https://developer.android.com/develop/ui/compose/layouts/adaptive/canonical-layouts)：上記の詳細説明。広い画面で一覧と詳細を並べ、狭い画面で切り替えること、主内容を助ける補助領域、幅の変化に伴う状態保持の参考。WebでComposeの導入は不要。

## navigation

- [Apple HIG — Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)：全体の行き先を切り替えるナビと、現在の画面への操作を区別する。NaSのWeb PoCに下部ナビの常設を要求するものではない。
- [Apple Developer — Toolbars](https://developer.apple.com/documentation/SwiftUI/Toolbars)：頻繁に使うコマンドや操作への入口という役割を参照する。Webのツールバーの位置は作業対象との関係から決める。

## forms

- [W3C WAI — Multi-page Forms](https://www.w3.org/WAI/tutorials/forms/multi-page/)：長い入力を論理的なまとまりで分けること、進捗と任意の段階を示すこと、完了済みの段階へ戻る際も入力を保つことの参考。短いフォームまで分割する根拠にはしない。

## reflow

- [W3C — Understanding SC 1.4.10: Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)：320 CSS px相当の幅で内容や機能を失わせないこと、二次元配置が必要な部分の例外とその範囲。表やキャンバスの例外を、周囲のフォームやページ全体へ広げない。固定部品が内容やフォーカスを隠す問題にも注意する。

## dialogs

- [W3C WAI-ARIA APG — Dialog (Modal) Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)：モーダル内でのキーボード移動、Escape、初期フォーカス、閉じた後の復帰、名前の関連付けの実装を参照する。モーダルは背後の操作を止めるため、主作業を並行して見る必要がある場合の選択は慎重に判断する。

## appearance

- [Apple HIG — Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Apple — Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/)

素材と操作層の表現を参考にする。淡い青、控えめな丸み、読みやすい不透明な本文面、NaSロゴを入れないこと、根拠のない文字アバターを作らないことは、この対話で決めたNaS独自の方針。

## 適用と確認

構成を選ぶ際は、この整理を出発点にする。プラットフォーム固有の仕様や実装APIの正確な挙動が判断に関わる場合は、その時点の公式資料を確認する。実際の利用者や主要経路での検証を行っていなければ、最適性やユーザビリティを実証したとは説明しない。
