from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

from rebalancr.database.db_manager import DatabaseManager
from rebalancr.intelligence.agent_kit.wallet_provider import get_wallet_provider
from rebalancr.config import settings


# Initialize router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)

# Initialize dependencies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
db_manager = DatabaseManager()

# Pydantic models
class User(BaseModel):
    user_id: str
    wallet_address: str
    email: Optional[str] = None
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    user_id: Optional[str] = None
    
class ActivateAgentRequest(BaseModel):
    settings: Optional[Dict[str, Any]] = None
    
# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception
    return token_data.user_id

# def get_current_user_id(some_parameters):
#     # Implementation
#     return user_id

# Authentication endpoints
@router.post("/login-with-ethereum", response_model=Token)
async def login_with_ethereum(wallet_address: str, signature: str):
    """
    Authenticate user with Ethereum wallet and signature
    """
    # Verify signature (implementation depends on your specific requirements)
    is_valid = verify_ethereum_signature(wallet_address, signature)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get or create user
    user = await db_manager.get_user_by_wallet(wallet_address)
    if not user:
        user_id = await db_manager.create_user(wallet_address)
    else:
        user_id = user["user_id"]
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await db_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user_id: str = Depends(get_current_user_id)):
    """
    Get current authenticated user information
    """
    user = await db_manager.get_user(current_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/activate-agent")
async def activate_agent(
    request: ActivateAgentRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Activate the portfolio agent for a user by creating
    a dedicated Privy wallet for agent operations
    """
    # Check if user already has an agent wallet
    existing_wallet = await db_manager.get_agent_wallet(user_id)
    if existing_wallet:
        return {"status": "success", "message": "Agent already activated"}
    
    # Create a new wallet using wallet provider
    wallet_provider = get_wallet_provider()
    
    # Save wallet association with user
    wallet_address = wallet_provider.get_address()
    await db_manager.save_agent_wallet(user_id, wallet_address)
    
    # Initialize agent settings with default values or user-provided values
    agent_settings = request.settings or {
        "auto_rebalance": False,
        "rebalance_threshold": 5.0,  # 5% deviation
        "max_gas_limit": "moderate"
    }
    
    await db_manager.initialize_agent_settings(user_id, agent_settings)
    
    return {
        "status": "success", 
        "message": "Agent activated successfully",
        "wallet_address": wallet_address
    }

@router.post("/deactivate-agent")
async def deactivate_agent(user_id: str = Depends(get_current_user_id)):
    """
    Deactivate the portfolio agent for a user
    """
    # Check if user has an agent wallet
    existing_wallet = await db_manager.get_agent_wallet(user_id)
    if not existing_wallet:
        return {"status": "error", "message": "Agent not activated"}
    
    # Deactivate agent
    await db_manager.deactivate_agent_wallet(user_id)
    
    return {
        "status": "success",
        "message": "Agent deactivated successfully"
    }

# Helper functions
def verify_ethereum_signature(wallet_address: str, signature: str) -> bool:
    """
    Verify that the signature was signed by the specified Ethereum address
    
    Implementation depends on your specific requirements
    """
    # This is a placeholder - you would implement actual signature verification here
    # using libraries like eth-account or web3.py
    # Example:
    # from eth_account.messages import encode_defunct
    # from web3.auto import w3
    # message = encode_defunct(text="Sign this message to prove wallet ownership")
    # signer = w3.eth.account.recover_message(message, signature=signature)
    # return signer.lower() == wallet_address.lower()
    
    return True  # For development/testing only 