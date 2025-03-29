import asyncio
import time
import json
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
async def test_wallet_methods():
    """Test various wallet methods"""
    logger.info("Starting wallet methods test")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    # Test cases with results
    results = {}
    
    # 1. Test wallet creation
    test_user_id = f"test_user_{int(time.time())}"  # Unique ID
    logger.info(f"Testing wallet creation for user: {test_user_id}")
    
    try:
        wallet_data = await wallet_provider.create_wallet(test_user_id)
        logger.info(f"Wallet created: {wallet_data.get('address')}")
        results["create_wallet"] = wallet_data
    except Exception as e:
        logger.error(f"Error creating wallet: {str(e)}", exc_info=True)
        results["create_wallet"] = {"error": str(e)}
    
    # 2. Test signature
    message = "Test message for signing"
    logger.info(f"Testing message signing: '{message}'")
    
    try:
        signature = await wallet_provider.sign_message(message)
        logger.info(f"Message signed successfully: {signature}")
        results["sign_message"] = signature
    except Exception as e:
        logger.error(f"Error signing message: {str(e)}", exc_info=True)
        results["sign_message"] = {"error": str(e)}
    
    # 3. Test transaction preparation
    tx = {
        "to": "0x0000000000000000000000000000000000000000",
        "value": 0,
        "data": "0x"
    }
    logger.info(f"Testing transaction preparation: {tx}")
    
    try:
        prepared_tx = wallet_provider._prepare_transaction(tx)
        logger.info(f"Transaction prepared: {prepared_tx}")
        results["prepare_tx"] = prepared_tx
    except Exception as e:
        logger.error(f"Error preparing transaction: {str(e)}", exc_info=True)
        results["prepare_tx"] = {"error": str(e)}
    
    # 4. Test wallet export
    logger.info("Testing wallet export")
    
    try:
        exported_wallet = wallet_provider.export_wallet()
        logger.info("Wallet exported successfully")
        results["export_wallet"] = exported_wallet
    except Exception as e:
        logger.error(f"Error exporting wallet: {str(e)}", exc_info=True)
        results["export_wallet"] = {"error": str(e)}
    
    logger.info("Wallet methods test completed")
    return results

if __name__ == "__main__":
    logger.info("Running wallet methods test directly")
    results = asyncio.run(test_wallet_methods())
    
    # Pretty print results
    formatted_results = json.dumps(results, indent=2)
    logger.info(f"Test completed with results: {formatted_results}") 