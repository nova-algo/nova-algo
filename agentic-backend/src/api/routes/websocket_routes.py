from fastapi import APIRouter, WebSocket, Depends
from ...websockets.websocket_handlers import handle_chat_websocket

from ...websockets.websocket_manager import websocket_manager

router = APIRouter()

# @router.websocket("/ws/{user_id}")
# async def websocket_endpoint(websocket: WebSocket, user_id: str):
#     await handle_chat_websocket(websocket, user_id) 