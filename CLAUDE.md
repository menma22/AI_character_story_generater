# Project Local Skills

このプロジェクトでは、特定のタスクを効率的かつ確実に行うためのローカルエージェントスキルを使用します。

## 使用可能なスキル

### [backend-management](file:///c:/Users/mahim/.gemini/antigravity/scratch/AI_character_story_generater/.agents/skills/backend-management/SKILL.md)
**用途**: バックエンドサーバーの起動、停止、状態確認、およびポート競合（8001番ポート）の解決。
**トリガー**: 「サーバーを起動して」「再起動して」「プロセスを止めて」などの依頼があった場合や、起動時にポート競合エラーが発生した場合。

---
エージェントへの指示:
バックエンド関連の操作を行う際は、必ず上記の `SKILL.md` を読み込み、そこに記載された標準手順（`python -m backend.main` の使用や、`taskkill` によるクリーンアップ）に従ってください。
