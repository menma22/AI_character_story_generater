# アプリケーション起動ステータス

- **最終起動日時**: 2026-04-18 17:40 (JST)
- **ポート**: 8001
- **PID**: 21236
- **実行コマンド**: `python -u -m backend.main`
- **最新の状態**: プロセス再起動完了 (2026-04-18 17:40)
- **詳細**: ポート 8001 にて新規プロセス (PID 21236) を起動。動作確認済み。
- **停止方法**: 
  - ポート 8001 を使用している PID を特定し、`taskkill /F /PID <PID>` で終了。
  - または `taskkill /F /IM python.exe` で全ての Python プロセスを終了。
  - WMI を使用して、特定の `python.exe`（uvicorn 等）を特定して終了させるのが確実。
- **現在の状態**: 正常起動中。使用コマンド: `python -u -m backend.main 2>&1 | Out-File -Encoding utf8 server_stdout.log`
