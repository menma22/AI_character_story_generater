# アプリケーション起動ステータス

- **最終起動日時**: 2026-04-18 18:39 (JST)
- **ポート**: 8001
- **PID**: 15228
- **実行コマンド**: `python -m backend.main`
- **最新の状態**: プロセス再起動完了 (2026-04-18 18:39) - IndentationError 修正後
- **詳細**: `backend/agents/daily_loop/activation.py` の IndentationError を修正し、ポート 8001 にて新規プロセス (PID 15228) を起動。
- **停止方法**: 
  - ポート 8001 を使用している PID を特定し、`taskkill /F /PID <PID>` で終了。
  - または `taskkill /F /IM python.exe` で全ての Python プロセスを終了。
- **現在の状態**: 正常起動中。使用コマンド: `powershell -Command "python -m backend.main 2>&1 | Out-File -Encoding utf8 server_stdout.log"`
