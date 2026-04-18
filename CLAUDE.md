# Project Local Skills

このプロジェクトでは、特定のタスクを効率的かつ確実に行うためのローカルエージェントスキルを使用します。

## 使用可能なスキル

### [backend-management](file:///c:/Users/mahim/.gemini/antigravity/scratch/AI_character_story_generater/.agents/skills/backend-management/SKILL.md)
**用途**: バックエンドサーバーの起動、停止、状態確認、およびポート競合（8001番ポート）の解決。
**トリガー**: 「サーバーを起動して」「再起動して」「プロセスを止めて」などの依頼があった場合や、起動時にポート競合エラーが発生した場合。

---
エージェントへの指示:
バックエンド関連の操作を行う際は、必ず上記の `SKILL.md` を読み込み、そこに記載された標準手順（`python -m backend.main` の使用や、`taskkill` によるクリーンアップ）に従ってください。

## 使用可能な MCP サーバー

### repomix MCP
**用途**: リポジトリ全体をパッケージ化し、コードベースの全体像（構造・依存関係・実装内容）を一度に把握する。
**登録コマンド**: `claude mcp add repomix -- npx -y repomix --mcp`
**主な提供ツール**: `pack_codebase`（ローカルディレクトリのパッキング）、`pack_remote_repository`（GitHub リポジトリのパッキング）、`read_repomix_output`、`grep_repomix_output`、`file_system_read_file`、`file_system_read_directory`。

---
エージェントへの指示（必須）:
**コードの全体像を把握する必要がある場合は、必ず repomix MCP を使用してください。** 具体的には以下のケースで、Glob/Grep/Read を個別に多数回呼び出す前に repomix MCP の `pack_codebase` を優先して実行します。

- プロジェクト初見時のアーキテクチャ把握
- 大規模リファクタリングや横断的な変更の設計前調査
- 複数ファイルにまたがる依存関係・呼び出し関係の確認
- 「コード全体を見て」「構造を教えて」「全体像を把握して」等の依頼を受けた時
- 外部 GitHub リポジトリの調査（`pack_remote_repository` を使用）

パッキング後は `grep_repomix_output` で必要箇所のみを抽出し、context window を圧迫しないように運用してください。
