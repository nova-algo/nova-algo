import asyncio
import logging
import pytest
from rebalancr.config import Settings
from rebalancr.intelligence.agent_kit.wallet_provider import PrivyWalletProvider
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_sign_typed_data():
    """Test EIP-712 typed data signing."""
    logger.info("Starting EIP-712 typed data signing test")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    # Setup test user
    test_user_id = "test_user_eip712"
    logger.info(f"Creating/retrieving wallet for user: {test_user_id}")
    
    try:
        wallet_data = await wallet_provider.get_or_create_wallet(test_user_id)
        logger.info(f"Wallet created/retrieved: {wallet_data.get('address')}")
    except Exception as e:
        logger.error(f"Failed to create/retrieve wallet: {str(e)}", exc_info=True)
        raise
    
    # Prepare EIP-712 typed data
    logger.info("Preparing EIP-712 typed data")
    typed_data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"}
            ],
            "Message": [
                {"name": "content", "type": "string"}
            ]
        },
        "primaryType": "Message",
        "domain": {
            "name": "TestDApp",
            "version": "1",
            "chainId": wallet_provider.get_network().chain_id
        },
        "message": {
            "content": "Test message for signing"
        }
    }
    logger.debug(f"Typed data: {typed_data}")
    
    # Sign typed data
    logger.info("Signing typed data")
    try:
        signature = wallet_provider.sign_typed_data(typed_data)
        logger.info(f"EIP-712 signature: {signature}")
    except Exception as e:
        logger.error(f"Error signing typed data: {str(e)}", exc_info=True)
        raise
    
    # Verify non-empty signature
    assert signature is not None and len(signature) > 0
    logger.info("EIP-712 typed data signing test completed successfully")
    return {"success": True, "signature": signature}

@pytest.mark.asyncio
async def test_contract_read():
    """Test reading from a contract."""
    logger.info("Starting contract read test")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    # Get wallet
    test_user_id = "test_user_contract"
    logger.info(f"Creating/retrieving wallet for user: {test_user_id}")
    
    try:
        wallet_data = await wallet_provider.get_or_create_wallet(test_user_id)
        logger.info(f"Wallet created/retrieved: {wallet_data.get('address')}")
    except Exception as e:
        logger.error(f"Failed to create/retrieve wallet: {str(e)}", exc_info=True)
        raise
    
    # Use a well-known contract
    contract_address = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    logger.info(f"Testing contract read for address: {contract_address}")
    abi = [{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"}]
    
    try:
        # Read contract name
        logger.info("Reading contract name")
        name = wallet_provider.read_contract(
            contract_address=contract_address,
            abi=abi,
            function_name="name"
        )
        logger.info(f"Contract name: {name}")
        logger.info("Contract read test completed successfully")
        return {"success": True, "contract_name": name}
    except Exception as e:
        logger.error(f"Error reading contract: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

@pytest.mark.asyncio
async def test_wallet_error_scenarios():
    """Test error handling in wallet provider."""
    logger.info("Starting wallet error scenarios test")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    results = {}
    
    # Test 1: Nonexistent wallet
    logger.info("Testing error handling for nonexistent wallet")
    try:
        address = wallet_provider.get_address()
        results["nonexistent_wallet"] = "Failed: Should have raised error"
        logger.warning("Nonexistent wallet test failed - no error was raised")
    except ValueError as e:
        results["nonexistent_wallet"] = "Success: Properly caught error"
        logger.info(f"Nonexistent wallet test passed - caught error: {str(e)}")
    
    # Test 2: Invalid transaction parameters
    logger.info("Testing error handling for invalid transaction parameters")
    try:
        await wallet_provider.get_or_create_wallet("test_error_user")
        logger.debug("Created test wallet for error testing")
        
        tx = {
            "to": "invalid-address",  # Invalid format
            "value": -1,  # Negative value
        }
        logger.debug(f"Attempting to send invalid transaction: {tx}")
        
        wallet_provider.send_transaction(tx)
        results["invalid_tx"] = "Failed: Should have raised error"
        logger.warning("Invalid transaction test failed - no error was raised")
    except Exception as e:
        results["invalid_tx"] = "Success: Properly caught error"
        logger.info(f"Invalid transaction test passed - caught error: {str(e)}")
    
    logger.info("Wallet error scenarios test completed")
    return results

@pytest.mark.asyncio
async def test_sign_message():
    """Test message signing."""
    logger.info("Starting message signing test")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    # Setup test user
    test_user_id = "test_user_sign_message"
    logger.info(f"Creating/retrieving wallet for user: {test_user_id}")
    
    try:
        wallet_data = await wallet_provider.get_or_create_wallet(test_user_id)
        logger.info(f"Wallet created/retrieved: {wallet_data.get('address')}")
    except Exception as e:
        logger.error(f"Failed to create/retrieve wallet: {str(e)}", exc_info=True)
        raise
    
    # Prepare test message
    test_message = "Hello, this is a test message for signing!"
    logger.info(f"Prepared message to sign: {test_message}")
    
    # Sign message
    logger.info("Signing message")
    try:
        signature = await wallet_provider.sign_message(test_message)
        logger.info(f"Message signature: {signature}")
    except Exception as e:
        logger.error(f"Error signing message: {str(e)}", exc_info=True)
        raise
    
    # Verify non-empty signature
    assert signature is not None and len(signature) > 0
    assert signature.startswith("0x")  # Ensure it's a hex string
    logger.info("Message signing test completed successfully")
    return {"success": True, "signature": signature}

@pytest.mark.asyncio
async def test_sign_transaction():
    """Test transaction signing."""
    logger.info("Starting transaction signing test")
    
    settings = Settings()
    logger.debug("Settings initialized")
    
    try:
        wallet_provider = PrivyWalletProvider.get_instance(settings)
        logger.info("Wallet provider initialized")
    except Exception as e:
        logger.error(f"Failed to initialize wallet provider: {str(e)}", exc_info=True)
        raise
    
    # Setup test user
    test_user_id = "test_user_123"
    logger.info(f"Creating/retrieving wallet for user: {test_user_id}")
    
    try:
        wallet_data = await wallet_provider.get_or_create_wallet(test_user_id)
        wallet_address = wallet_data.get('address')
        logger.info(f"Wallet created/retrieved: {wallet_address}")
    except Exception as e:
        logger.error(f"Failed to create/retrieve wallet: {str(e)}", exc_info=True)
        raise
    
    # Create a test transaction (not sending, just signing)
    # Use a dummy address for testing
    test_recipient = "0x5e869af2Af006B538f9c6D231C31DE7cDB4153be"
    test_amount = 0  # 0 ETH - we're just testing signing, not sending
    
    # Create transaction parameters
    # tx_params = {
    #     'from': wallet_address,
    #     'to': Web3.to_checksum_address(test_recipient),
    #     'value': test_amount,
    #     'data': b'',
    #     'chainId': wallet_provider.get_network().chain_id,
    # }

    tx_params = {
        'from': wallet_address,
        'to': Web3.to_checksum_address(test_recipient),
        'value': test_amount,
        #'data': b'',
        #'chainId': wallet_provider.get_network().chain_id,
        'chainId': 84532,
        'type': 2,  # EIP-1559 transaction
        'gas_limit': "0x5208",  # Standard ETH transfer
        'nonce': 1,  # This might need to be obtained dynamically
        'max_fee_per_gas': "0x14bf7dadac",
        'max_priority_fee_per_gas': "0xf4240"
    }
    
    logger.info(f"Prepared transaction for signing: {tx_params}")
    
    # Sign transaction
    logger.info("Signing transaction")
    try:
        signed_tx = wallet_provider.sign_transaction(tx_params)
        logger.info("Transaction signature obtained")
        logger.debug(f"Signed transaction: {signed_tx}")
    except Exception as e:
        logger.error(f"Error signing transaction: {str(e)}", exc_info=True)
        raise
    
    # Verify signature
    assert signed_tx is not None
    assert hasattr(signed_tx, 'rawTransaction')
    
    logger.info("Transaction signing test completed successfully")
    return {"success": True}

if __name__ == "__main__":
    logger.info("Running EIP-712 typed data signing test directly")
    result = asyncio.run(test_sign_typed_data())
    logger.info(f"Test completed with result: {result}")
    
    logger.info("Running message signing test directly")
    result = asyncio.run(test_sign_message())
    logger.info(f"Test completed with result: {result}")
    
    logger.info("Running transaction signing test directly")
    result = asyncio.run(test_sign_transaction())
    logger.info(f"Test completed with result: {result}")
    
    logger.info("Running contract read test directly")
    result = asyncio.run(test_contract_read())
    logger.info(f"Test completed with result: {result}")
    
    logger.info("Running wallet error scenarios test directly")
    result = asyncio.run(test_wallet_error_scenarios())
    logger.info(f"Test completed with result: {result}")
