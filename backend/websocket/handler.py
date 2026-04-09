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
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active: {len(self.active_connections)}")
    
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
    
    async def send_agent_thought(self, agent_name: str, content: str, status: str = "thinking"):
        """エージェントの思考をストリーミング"""
        await self.broadcast({
            "type": "agent_thought",
            "agent": agent_name,
            "content": content,
            "status": status,  # thinking / complete / error
        })
    
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
