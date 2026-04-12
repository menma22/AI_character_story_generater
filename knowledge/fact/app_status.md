# アプリケーション起動ステータス

- **最終起動日時**: 2026-04-12 17:34 (JST)
- **ポート**: 8001
- **実行コマンド**: `python -m backend.main`
- **停止方法**: 
  - ポート 8001 を使用している PID を特定し、`taskkill /F /PID <PID>` で終了。
  - または `taskkill /F /IM python.exe` で全ての Python プロセスを終了。
  - WMI を使用して、特定の `python.exe`（uvicorn 等）を特定して終了させるのが確実。
- **現在の状態**: 正常起動中。WebSocket 接続が確立されている。
