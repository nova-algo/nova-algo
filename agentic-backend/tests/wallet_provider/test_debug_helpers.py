import os
import json
import asyncio
import aiohttp
import logging
import pytest
from rebalancr.intelligence.agent_kit.wallet_provider import PrivyWalletProvider
from rebalancr.config import Settings

# Enhanced logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_wallet_files(wallet_provider, user_id):
    """Check if wallet files exist and show their contents"""
    logger.info(f"Checking wallet files for user: {user_id}")
    path = wallet_provider._get_wallet_path(user_id)
    logger.debug(f"Wallet path: {path}")
    
    if os.path.exists(path):
        logger.info(f"Wallet file found at: {path}")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Wallet file contents: {json.dumps(data, indent=2)}")
            return True
        except Exception as e:
            logger.error(f"Error reading wallet file: {str(e)}", exc_info=True)
            return False
    else:
        logger.warning(f"No wallet file found at: {path}")
        return False

async def test_network_connectivity(wallet_provider):
    """Test connectivity to the blockchain network"""
    logger.info("Testing network connectivity")
    
    chain_id = wallet_provider._get_chain_id_from_network_id(wallet_provider.network_id)
    rpc_url = wallet_provider._get_rpc_url_for_network(wallet_provider.network_id)
    
    logger.info(f"Testing connectivity to: {rpc_url} (Chain ID: {chain_id})")
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.debug("Sending JSON-RPC request to get block number")
            async with session.post(
                rpc_url,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
            ) as response:
                data = await response.json()
                logger.debug(f"Network response: {data}")
                
                if "result" in data:
                    logger.info(f"Network connection successful - block number: {data['result']}")
                    return True
                else:
                    logger.warning(f"Network response missing result field: {data}")
                    return False
    except Exception as e:
        logger.error(f"Network connectivity test failed: {str(e)}", exc_info=True)
        return False

@pytest.mark.asyncio
async def test_run_debug_tests():
    """Run all debugging tests"""
    logger.info("Starting debug helper tests")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    # Test user ID
    test_user_id = "test_user_123"
    
    # 1. Check network connectivity
    logger.info("Testing network connectivity")
    network_connected = await test_network_connectivity(wallet_provider)
    logger.info(f"Network connectivity: {'✅ Success' if network_connected else '❌ Failed'}")
    
    # 2. Ensure user has a wallet
    logger.info(f"Creating/retrieving wallet for user: {test_user_id}")
    try:
        wallet_data = await wallet_provider.get_or_create_wallet(test_user_id)
        logger.info(f"Wallet address: {wallet_data.get('address')}")
    except Exception as e:
        logger.error(f"Failed to create/retrieve wallet: {str(e)}", exc_info=True)
        raise
    
    # 3. Check wallet files
    logger.info("Checking wallet files")
    wallet_files_exist = check_wallet_files(wallet_provider, test_user_id)
    logger.info(f"Wallet files check: {'✅ Found' if wallet_files_exist else '❌ Not found'}")
    
    # 4. Print network settings
    logger.info("Checking network settings")
    network_id = wallet_provider.network_id
    chain_id = wallet_provider._get_chain_id_from_network_id(network_id)
    rpc_url = wallet_provider._get_rpc_url_for_network(network_id)
    
    logger.info(f"Network ID: {network_id}")
    logger.info(f"Chain ID: {chain_id}")
    logger.info(f"RPC URL: {rpc_url}")
    
    logger.info("Debug helper tests completed successfully")
    return {
        "success": True,
        "network_connected": network_connected,
        "wallet_address": wallet_data.get('address'),
        "wallet_files_exist": wallet_files_exist,
        "network_id": network_id,
        "chain_id": chain_id
    }

if __name__ == "__main__":
    logger.info("Running debug helper tests directly")
    result = asyncio.run(test_run_debug_tests())
    logger.info(f"Tests completed with result: {result}") 