"""
WebSocket ハンドラ
エージェントの思考過程をリアルタイムでフロントエンドにストリーミングする
"""

import json
import asyncio
import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket接続管理"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.thought_history: list[dict] = []  # 現在のセッションの思考ログ
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        # 同一オブジェクトの重複登録防止
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected (ID:{id(websocket)}). Active: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected (ID:{id(websocket)}). Active: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """全接続にメッセージをブロードキャスト"""
        disconnected = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_agent_thought(self, agent_name: str, content: str, status: str = "thinking", model: Optional[str] = None):
        """エージェントの思考をストリーミング"""
        payload = {
            "type": "agent_thought",
            "agent": agent_name,
            "content": content,
            "status": status,  # thinking / complete / error
            "model": model,    # 使用されたLLMモデル名
        }
        self.thought_history.append(payload)
        await self.broadcast(payload)
    
    def clear_history(self):
        """ログ履歴をクリア"""
        self.thought_history = []
    
    async def send_progress(self, phase: str, progress: float, detail: str = ""):
        """進捗更新"""
        await self.broadcast({
            "type": "progress",
            "phase": phase,
            "progress": progress,
            "detail": detail,
        })
    
    async def send_phase_result(self, phase: str, result: dict):
        """Phase完了結果"""
        await self.broadcast({
            "type": "phase_result",
            "phase": phase,
            "result": result,
        })
    
    async def send_diary_entry(self, day: int, content: str):
        """日記エントリのストリーミング"""
        await self.broadcast({
            "type": "diary_entry",
            "day": day,
            "content": content,
        })
    
    async def send_error(self, error: str):
        """エラー通知"""
        await self.broadcast({
            "type": "error",
            "content": error,
        })
    
    async def send_cost_update(self, cost_data: dict):
        """コスト情報更新"""
        await self.broadcast({
            "type": "cost_update",
            "data": cost_data,
        })


# グローバルインスタンス
manager = ConnectionManager()
