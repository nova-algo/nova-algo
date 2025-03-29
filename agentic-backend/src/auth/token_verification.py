from fastapi import WebSocket, WebSocketDisconnect, status
import jwt
from jwt import PyJWTError, PyJWT
import logging
import json
from ..config import get_settings

logger = logging.getLogger(__name__)

async def verify_privy_token(token: str, expected_user_id: str = None) -> dict:
    """
    Verify a Privy authentication token
    
    Args:
        token: Privy JWT token
        expected_user_id: Optional user ID to validate against
        
    Returns:
        Dict with validation result
    """
    config = get_settings()
    try:
        # Get the verification key from settings
        verification_key = config.PRIVY_VERIFICATION_KEY
        
        # Verify JWT properly
        decoded = jwt.decode(
            token,
            verification_key,  
            issuer='privy.io',
            audience=config.PRIVY_APP_ID,
            algorithms=['ES256']
        )
        
        # Get the user's Privy DID from the subject claim
        user_id = decoded.get('sub')
        
        # If expected_user_id is provided, verify it matches
        if expected_user_id and user_id != expected_user_id:
            return {"is_valid": False, "error": "User ID mismatch"}
            
        return {"is_valid": True, "user_id": user_id}
    except PyJWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        return {"is_valid": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return {"is_valid": False, "error": str(e)}