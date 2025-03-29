from fastapi import WebSocket, WebSocketDisconnect, status
import logging
import json
from ..config import get_settings
from ..auth.token_verification import verify_privy_token
logger = logging.getLogger(__name__)

async def authenticate_websocket(websocket: WebSocket) -> dict:
    """
    Authenticate a WebSocket connection using Privy
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        Dict with authentication result and user_id
    """
    try:
        # Wait for auth message
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)
        
        # Check if auth data has token
        if "type" not in auth_data or auth_data["type"] != "auth":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return {"success": False, "error": "Invalid auth message"}
        
        if "token" not in auth_data:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return {"success": False, "error": "Missing auth token"}
        
        # Verify token
        token_result = await verify_privy_token(auth_data["token"])
        if not token_result["is_valid"]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return {"success": False, "error": token_result.get("error")}
        
        # Return user ID from token
        return {
            "success": True,
            "user_id": token_result["user_id"]
        }
    except WebSocketDisconnect:
        return {"success": False, "error": "Client disconnected during authentication"}
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return {"success": False, "error": str(e)}
