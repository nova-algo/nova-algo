import asyncio
from decimal import Decimal
import logging
import pytest
from rebalancr.intelligence.agent_kit.wallet_provider import PrivyWalletProvider
from rebalancr.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_transaction():
    """Test sending a transaction with the wallet provider"""
    logger.info("Starting wallet transaction test")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    # Get user wallet
    test_user_id = "test_user_123"
    logger.info(f"Creating/retrieving wallet for user: {test_user_id}")
    
    try:
        wallet_data = await wallet_provider.get_or_create_wallet(test_user_id)
        logger.info(f"Wallet created/retrieved: {wallet_data.get('address')}")
    except Exception as e:
        logger.error(f"Failed to create/retrieve wallet: {str(e)}", exc_info=True)
        raise
    
    # Check initial balance
    try:
        initial_balance = wallet_provider.get_balance()
        logger.info(f"Initial balance: {initial_balance}")
    except Exception as e:
        logger.error(f"Failed to get initial balance: {str(e)}", exc_info=True)
        raise
    
    # Send a small amount to a test address (zero address for testing)
    test_address = "0x5e869af2Af006B538f9c6D231C31DE7cDB4153be"
    amount = Decimal("0.01") * Decimal("1e18")  # 0.01 ETH in wei
    logger.info(f"Preparing to send {amount} to {test_address}")
    
    try:
        # Execute transfer
        logger.info("Executing native transfer")
        tx_hash = wallet_provider.native_transfer(test_address, amount)
        logger.info(f"Transaction sent: {tx_hash}")
        
        # Wait for receipt
        logger.info("Waiting for transaction receipt")
        receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)
        logger.debug(f"Transaction receipt: {receipt}")
        logger.info(f"Transaction confirmed in block {receipt.get('blockNumber')}")
        
        # Check new balance
        logger.info("Checking new balance")
        new_balance = wallet_provider.get_balance()
        logger.info(f"New balance: {new_balance}")
        
        # Calculate and log the difference
        balance_diff = initial_balance - new_balance
        logger.info(f"Balance difference: {balance_diff}")
        
        logger.info("Transaction test completed successfully")
        return {
            "success": True,
            "tx_hash": tx_hash,
            "initial_balance": str(initial_balance),
            "new_balance": str(new_balance),
            "difference": str(balance_diff)
        }
    except Exception as e:
        logger.error(f"Transaction failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    logger.info("Running wallet transaction test directly")
    result = asyncio.run(test_transaction())
    logger.info(f"Test completed with result: {result}") 