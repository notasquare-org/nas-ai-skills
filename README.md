# NaS AI Skills

Not a Squareで利用するAI Skillと会社コンテキストの正本です。

## 収録内容

- `nas-slides/`: NaS正式トンマナで編集可能なスライドを制作・検証するSkill
- `nas-poc-ui/`: 用途と操作の流れから画面構成を選び、淡い青とガラス表現でNaSの商談用Web PoCを統一するUI Skill（配置ガイド・配色CSS・PC／スマホの画面見本付き）
- `cloudflare-os-build-gadget/`: Cloudflare OS Gadgetを設計・梱包・検証するSkill
- `company-context/`: NaSの会社情報と、確定・未確定事項の基礎コンテキスト

## 運用ルール

1. 変更はこのリポジトリを起点に行う。
2. Skillはフォルダ単位でレビューし、`SKILL.md`から必要な参照・スクリプトへ到達できる状態を保つ。
3. Cloudflare OSには、レビュー済みのコミットに含まれるファイルだけを反映する。
4. APIキー、OAuthトークン、顧客データ、会話履歴、決済情報を保存しない。
5. Notionは人が読む会社情報の原本、Google Driveはロゴ・画像・スライドなどの資産置き場として扱う。

## Codexでの利用

利用するSkillフォルダをCodexのSkillsディレクトリへ配置します。会社コンテキストは必要な業務だけで参照し、外部送信や共有範囲の変更には別途承認を残します。
