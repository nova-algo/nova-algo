from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from ...websockets.auth import verify_privy_token  # Reuse the verification function

async def privy_auth_middleware(request: Request, call_next):
    """
    Middleware to verify Privy authentication tokens
    
    Args:
        request: FastAPI request
        call_next: Next middleware function
    """
    # Skip auth for certain paths
    path = request.url.path
    if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
        return await call_next(request)
    
    # WebSocket endpoints handled separately
    if path.startswith("/ws"):
        return await call_next(request)
    
    # Check for auth header (Privy token is in Authorization header when using local storage)
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid Authorization header format"}
        )
    
    # Extract token
    token = auth_header.replace("Bearer ", "")
    
    # Verify token
    token_result = await verify_privy_token(token)
    
    if not token_result["is_valid"]:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": f"Invalid authentication: {token_result.get('error')}"}
        )
    
    # Add user_id to request state for handlers to access
    request.state.user_id = token_result["user_id"]
    
    # Continue with request
    return await call_next(request)
