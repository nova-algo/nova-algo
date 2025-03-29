import asyncio
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
async def test_wallet_provider():
    """Test basic wallet provider functionality"""
    logger.info("Starting wallet provider test")
    
    # 1. Initialize settings
    settings = Settings()
    logger.debug("Settings initialized")
    
    # 2. Get wallet provider instance
    logger.info("Initializing wallet provider")
    wallet_provider = PrivyWalletProvider.get_instance(settings)
    logger.info("Wallet provider initialized successfully")
    
    # 3. Test user wallet creation and retrieval
    test_user_id = "test_user_123"
    logger.info(f"Testing wallet creation for user: {test_user_id}")
    
    try:
        wallet_data = await wallet_provider.get_or_create_wallet(test_user_id)
        logger.info(f"Wallet created/retrieved: {wallet_data.get('address')}")
    except Exception as e:
        logger.error(f"Failed to create/retrieve wallet: {str(e)}", exc_info=True)
        raise
    
    # 4. Check wallet balance
    try:
        balance = wallet_provider.get_balance()
        logger.info(f"Wallet balance: {balance}")
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {str(e)}", exc_info=True)
        raise
    
    # 5. Test wallet address retrieval
    try:
        address = wallet_provider.get_address()
        logger.info(f"Wallet address: {address}")
    except Exception as e:
        logger.error(f"Failed to get wallet address: {str(e)}", exc_info=True)
        raise
    
    # 6. Test network retrieval
    try:
        network = wallet_provider.get_network()
        logger.info(f"Network: {network.network_id}, chain ID: {network.chain_id}")
    except Exception as e:
        logger.error(f"Failed to get network: {str(e)}", exc_info=True)
        raise
    
    logger.info("Wallet provider test completed successfully")
    return {
        "success": True,
        "address": address,
        "balance": balance,
        "network": network
    }

if __name__ == "__main__":
    logger.info("Running wallet provider test directly")
    result = asyncio.run(test_wallet_provider())
    logger.info(f"Test completed with result: {result}") 