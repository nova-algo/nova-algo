from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, Optional

from ...intelligence.agent_kit.agent_manager import AgentManager
from ..dependencies import get_agent_manager

router = APIRouter(prefix="/wallets", tags=["wallets"])

@router.get("/{user_id}/info")
async def get_wallet_info(
    user_id: str,
    request: Request,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Get wallet information for a user
    
    This endpoint requires authentication and the user_id must match the authenticated user.
    """
    # Get the authenticated user ID from request state (set by auth middleware)
    authenticated_user_id = request.state.user_id
    
    # Verify that the authenticated user matches the requested user_id
    if authenticated_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own wallet information"
        )
    
    try:
        # Get wallet address for this user
        wallet_address = await agent_manager.wallet_provider.get_wallet_address(user_id)
        
        # Get wallet balance
        balance = await agent_manager.wallet_provider.get_balance(user_id)
        
        return {
            "address": wallet_address,
            "balance": balance
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving wallet information: {str(e)}"
        )

@router.post("/{user_id}/send")
async def send_transaction(
    user_id: str,
    transaction_data: Dict[str, Any],
    request: Request,
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Send a transaction from user's wallet
    
    This endpoint requires authentication and the user_id must match the authenticated user.
    """
    # Get the authenticated user ID from request state (set by auth middleware)
    authenticated_user_id = request.state.user_id
    
    # Verify that the authenticated user matches the requested user_id
    if authenticated_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only send transactions from your own wallet"
        )
    
    try:
        # Send transaction using the wallet provider
        result = await agent_manager.wallet_provider.send_transaction(user_id, transaction_data)
        
        return {
            "success": True,
            "transaction_id": result.get("transaction_id"),
            "status": result.get("status")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending transaction: {str(e)}"
        )




