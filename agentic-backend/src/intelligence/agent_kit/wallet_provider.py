"""Privy server wallet provider compatible with AgentKit."""

import json
import os
import uuid
import requests
import logging
from decimal import Decimal
from typing import Optional, Dict, List, Any, Union
from web3 import Web3
from web3.types import BlockIdentifier, ChecksumAddress, HexStr, TxParams

# Import from coinbase_agentkit
from coinbase_agentkit.wallet_providers.evm_wallet_provider import EvmWalletProvider, EvmGasConfig
from coinbase_agentkit.network import Network

from pydantic import BaseModel, Field
from ...config import get_settings

logger = logging.getLogger(__name__)

# Configuration class for Privy wallet provider
class PrivyProviderConfig(BaseModel):
    """Base configuration for Privy providers."""
    app_id: Optional[str] = Field(None, description="The Privy app ID")
    #api_key: Optional[str] = Field(None, description="The Privy API key")
    app_secret: Optional[str] = Field(None, description="The Privy app secret")

class PrivyWalletProviderConfig(PrivyProviderConfig):
    """Configuration for Privy wallet provider."""
    network_id: str = Field("base-sepolia", description="The network ID")
    wallet_data: Optional[str] = Field(None, description="The wallet data as a JSON string")
    gas: Optional[EvmGasConfig] = Field(None, description="Gas configuration settings")

# The Privy wallet provider that inherits from EvmWalletProvider
class PrivyWalletProvider(EvmWalletProvider):
    """
    Wallet provider that uses Privy Server Wallets for integration with AgentKit.
    
    This provider implements the EvmWalletProvider interface, enabling it to 
    work seamlessly with AgentKit while leveraging Privy's secure wallet infrastructure.
    """
    _instance = None  # Singleton pattern
    
    @classmethod
    def get_instance(cls, config=None):
        """Get singleton instance of PrivyWalletProvider"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def __init__(self, config=None):
        """Initialize the Privy wallet provider"""
        # Get settings from config or environment
        settings = get_settings()
        
        # Initialize configuration
        if not config:
            config = PrivyWalletProviderConfig(
                app_id=settings.PRIVY_APP_ID,
                #api_key=settings.PRIVY_API_KEY,
                network_id=settings.NETWORK_ID or "base-sepolia",
                app_secret=settings.PRIVY_APP_SECRET,
                gas=EvmGasConfig(
                    gas_limit_multiplier=1.2,
                    fee_per_gas_multiplier=1.2
                )
            )
        elif not isinstance(config, PrivyWalletProviderConfig):
            config = PrivyWalletProviderConfig(
                app_id=getattr(config, "PRIVY_APP_ID", None),
                app_secret=getattr(config, "PRIVY_APP_SECRET", None),
                network_id=getattr(config, "NETWORK_ID", "base-sepolia"),
                gas=EvmGasConfig(
                    gas_limit_multiplier=1.2,
                    fee_per_gas_multiplier=1.2
                )
            )
        
        # Validate required credentials
        if not config.app_id or not config.app_secret:
            raise ValueError("Missing Privy credentials. Set PRIVY_APP_ID and PRIVY_APP_SECRET in your environment.")
        
        self.config = config
        
        # Setup API and data directories
        self.base_url = "https://api.privy.io/v1"
        self.wallet_data_dir = os.path.join(settings.DATA_DIR, "wallets")
        os.makedirs(self.wallet_data_dir, exist_ok=True)
        
        # Get chain ID from network ID
        #chain_id = self._get_chain_id_from_network_id(config.network_id)
        chain_id =  "monad-testnet"
        # Setup Web3 connection with RPC URL
        #rpc_url = self._get_rpc_url_for_network(config.network_id)
        #rpc_url = "https://sepolia.base.org"

        #chain_id = "monad_testnet"
        rpc_url = "https://testnet-rpc.monad.xyz"
        self._web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Initialize network object (matches CDP wallet provider)
        self._network = Network(
            protocol_family="evm",
            network_id=config.network_id,
            chain_id=chain_id
        )
        
        # Initialize wallet-related attributes
        self._wallet_data = None
        self._address = None
        
        # Set gas configuration from config or defaults
        self._gas_limit_multiplier = (
            max(config.gas.gas_limit_multiplier, 1)
            if config.gas and config.gas.gas_limit_multiplier is not None
            else 1.2
        )
        
        self._fee_per_gas_multiplier = (
            max(config.gas.fee_per_gas_multiplier, 1)
            if config.gas and config.gas.fee_per_gas_multiplier is not None
            else 1.2
        )
        
        # If wallet data is provided in config, use it
        if config.wallet_data:
            try:
                self._wallet_data = json.loads(config.wallet_data)
                self._address = self._wallet_data.get("address")
            except json.JSONDecodeError:
                logger.error("Failed to parse wallet data JSON")
        
        logger.info(f"Initialized PrivyWalletProvider with app_id: {config.app_id}, network: {config.network_id}")
    
    def _get_chain_id_from_network_id(self, network_id: str) -> int:
        """Convert network ID to chain ID.
        
        Args:
            network_id: String identifier for the network (e.g. 'ethereum', 'base-sepolia')
            
        Returns:
            int: The corresponding chain ID for the network
        """
        network_map = {
            "ethereum": 1,
            "goerli": 5, 
            "sepolia": 11155111,
            "base": 8453,
            "base-sepolia": 84532,
            "optimism": 10,
            "arbitrum": 42161,
            "polygon": 137,
            "monad-testnet": 10143
        }
        
        chain_id = network_map.get(network_id)
        if chain_id is None:
            logger.warning(f"Unknown network ID: {network_id}, defaulting to Ethereum mainnet (1)")
            chain_id = 1
            
        return chain_id
    
    def _get_rpc_url_for_network(self, network_id: str) -> str:
        """Get RPC URL for the specified network"""
        # This would typically come from configuration
        # For now, using public RPC endpoints
        rpc_map = {
            "ethereum": "https://eth.llamarpc.com",
            "goerli": "https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
            "sepolia": "https://sepolia.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
            "base": "https://mainnet.base.org",
            "base-sepolia": "https://sepolia.base.org", 
            "optimism": "https://mainnet.optimism.io",
            "arbitrum": "https://arb1.arbitrum.io/rpc",
            "polygon": "https://polygon-rpc.com",
            "monad-testnet": "https://testnet-rpc.monad.xyz"
        }
        return rpc_map.get(network_id, rpc_map["ethereum"])
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers for Privy API authentication"""
        import base64
        
        # Create basic auth header from app ID and secret
        auth_str = f"{self.config.app_id}:{self.config.app_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Content-Type": "application/json",
            "privy-app-id": self.config.app_id,
            "Authorization": f"Basic {encoded_auth}"
        }
        
        # If you have an authorization key, would add privy-authorization-signature here
        
        return headers
    
    def _get_wallet_path(self, user_id: str) -> str:
        """Get path for storing wallet data for a user"""
        return os.path.join(self.wallet_data_dir, f"wallet-{user_id}.json")
    
    async def load_wallet_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load wallet data for a user"""
        wallet_path = self._get_wallet_path(user_id)
        
        if os.path.exists(wallet_path):
            try:
                with open(wallet_path, "r") as f:
                    wallet_data = json.load(f)
                logger.info(f"Loaded wallet data for user {user_id}")
                return wallet_data
            except Exception as e:
                logger.error(f"Error loading wallet data for user {user_id}: {str(e)}")
        
        return None
    
    async def save_wallet_data(self, user_id: str, wallet_data: Dict[str, Any]) -> None:
        """Save wallet data for a user"""
        wallet_path = self._get_wallet_path(user_id)
        
        try:
            with open(wallet_path, "w") as f:
                json.dump(wallet_data, f, indent=2)
            logger.info(f"Saved wallet data for user {user_id}")
        except Exception as e:
            logger.error(f"Error saving wallet data for user {user_id}: {str(e)}")
    
    async def create_wallet(self, user_id: str) -> Dict[str, Any]:
        """Create a new Privy server wallet for a user"""
        try:
            url = f"{self.base_url}/wallets"
            headers = self._get_auth_headers()
            idempotency_key = f"create-wallet-{user_id}-{uuid.uuid4()}"
            
            data = {
                "chain_type": "ethereum",
                "idempotency_key": idempotency_key,
                "policy": {
                    "name": f"User {user_id} wallet policy",
                    "description": f"Policy for user {user_id}'s wallet",
                    "rules": [
                        {
                            "type": "max_tx_amount",
                            "params": {
                                "amount": "1000000000000000000",  # 1 ETH in wei
                                "denomination": "wei"
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            wallet_data = response.json()
            await self.save_wallet_data(user_id, wallet_data)
            
            # Set wallet data for this instance if it's the first wallet
            if not self._wallet_data:
                self._wallet_data = wallet_data
                self._address = wallet_data.get("address")
            
            logger.info(f"Created new Privy wallet for user {user_id} with address: {wallet_data.get('address')}")
            return wallet_data
            
        except Exception as e:
            logger.error(f"Error creating Privy wallet: {str(e)}")
            raise
    
    async def get_or_create_wallet(self, user_id: str) -> Dict[str, Any]:
        """Get existing wallet or create a new one for the user"""
        wallet_data = await self.load_wallet_data(user_id)
        
        if not wallet_data or not wallet_data.get('id'):
            # No wallet exists, create a new one
            return await self.create_wallet(user_id)
        
        # Wallet exists, verify it's still valid
        try:
            wallet_id = wallet_data.get('id')
            url = f"{self.base_url}/wallets/{wallet_id}"
            #url = f"{self.base_url}/wallets/{wallet_id}/rpc"
            headers = self._get_auth_headers()
            
            response = requests.get(url, headers=headers)
            
            # Check for specific status codes
            if response.status_code == 404:
                # Wallet not found on Privy, create a new one
                logger.warning(f"Wallet {wallet_id} not found on Privy, creating new wallet")
                return await self.create_wallet(user_id)
            elif response.status_code != 200:
                # Other error occurred
                logger.error(f"Error fetching wallet: {response.status_code} {response.text}")
                raise Exception(f"Failed to fetch wallet info: {response.text}")
                
            wallet_data = response.json()
            
            # Set wallet data for this instance if it's the first wallet
            if not self._wallet_data:
                self._wallet_data = wallet_data
                self._address = wallet_data.get("address")
            
            # Update local wallet data
            await self.save_wallet_data(user_id, wallet_data)
            
            return wallet_data
        except Exception as e:
            logger.error(f"Error fetching wallet for user {user_id}: {str(e)}")
            # If we can't verify, try to create a new wallet
            return await self.create_wallet(user_id)
    
    # Required methods from EvmWalletProvider
    def get_address(self) -> str:
        """Get the wallet address"""
        if not self._address and self._wallet_data:
            self._address = self._wallet_data.get("address")
            
        if not self._address:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        return self._address
    
    def get_balance(self) -> Decimal:
        """Get wallet balance in native currency"""
        if not self._address:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        balance_wei = self._web3.eth.get_balance(self._address)
        return Decimal(str(balance_wei))
    
    def get_name(self) -> str:
        """Get provider name"""
        return "privy_wallet_provider"
    
    def get_network(self) -> Network:
        """Get the current network"""
        return self._network
    
    def native_transfer(self, to: str, value: Decimal) -> str:
        """Transfer native currency"""
        if not self._address:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        # Create transaction parameters
        tx_params = {
            'from': self._address,
            'to': Web3.to_checksum_address(to),
            'value': int(value),
            'data': b'',
            'chainId': self._network.chain_id,
        }
        
        # Send transaction via Privy API
        tx_hash = self.send_transaction(tx_params)
        return tx_hash
    
    async def sign_message(self, message: Union[str, bytes]) -> HexStr:
        """Sign a message with the wallet"""
        # if not self._wallet_data:
        #     raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        wallet_id = self._wallet_data.get('id')
        
        # Format request according to JSON-RPC style
        url = f"{self.base_url}/wallets/{wallet_id}/rpc"
        
        # Configure message format
        if isinstance(message, str):
            if message.startswith('0x'):
                encoding = "hex"
                message_value = message
            else:
                encoding = "utf-8" 
                message_value = message
        else:
            encoding = "hex"
            message_value = "0x" + message.hex()
        
        payload = {
            "chain_type": "ethereum",
            "method": "personal_sign",
            "params": {
                "message": message_value,
                "encoding": encoding
            }
        }
        
        try:
            headers = self._get_auth_headers()
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "data" in result and "signature" in result["data"]:
                return result["data"]["signature"]
            else:
                raise ValueError(f"Invalid response from Privy API: {result}")
            
        except Exception as e:
            logger.error(f"Error signing message: {str(e)}")
            raise
    
    def sign_typed_data(self, typed_data: Dict[str, Any]) -> HexStr:
        """Sign typed data according to EIP-712 standard"""
        if not self._wallet_data:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        wallet_id = self._wallet_data.get('id')
        
        try:
            url = f"{self.base_url}/wallets/{wallet_id}/rpc"
            headers = self._get_auth_headers()
            
            payload = {
                "typed_data": typed_data,
                "chain_id": str(self._network.chain_id)
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            if "data" in result and "signature" in result["data"]:
                return result["data"]["signature"]
            else:
                raise ValueError(f"Invalid response from Privy API: {result}")
            
            #return result.get("signature")
            
        except Exception as e:
            logger.error(f"Error signing typed data: {str(e)}")
            raise
    
    def sign_transaction(self, transaction: TxParams) -> HexStr:
        """Sign a transaction"""
        if not self._wallet_data:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        wallet_id = self._wallet_data.get('id')
        logger.info(f"Signing transaction for wallet {wallet_id}")
        # Prepare transaction
        prepared_tx = self._prepare_transaction(transaction)

        # Generate idempotency key based on transaction params
        idempotency_key = f"tx-{wallet_id}-{prepared_tx.get('nonce', '')}-{uuid.uuid4()}"
        
        try:
            url = f"{self.base_url}/wallets/{wallet_id}/rpc"
            headers = self._get_auth_headers()
            
            payload = {
                "method": "eth_signTransaction",  
                "params": {
                    "transaction": prepared_tx 
                },
                "idempotency_key": idempotency_key
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            # Check for HTTP errors
            if response.status_code != 200:
                raise Exception(f"Error signing transaction: {response.status_code} {response.text}")
            
            result = response.json()

              
            # Check if response contains expected data
            if "data" in result and "signature" in result["data"]:
                return result["data"]["signature"]
            else:
                raise ValueError(f"Invalid response from Privy API: {result}")    
            
            # # Check if response contains expected data
            # if "data" in result and "rawTransaction" in result["data"]:
            #     # Create a SignedTransaction object
            #     class PrivySignedTransaction:
            #         def __init__(self, raw_transaction):
            #             self.rawTransaction = raw_transaction
                
            #     # Convert hex string to bytes if needed
            #     raw_tx = result["data"]["rawTransaction"]
            #     if isinstance(raw_tx, str) and raw_tx.startswith("0x"):
            #         raw_tx = bytes.fromhex(raw_tx[2:])
                    
            #     return PrivySignedTransaction(raw_tx)
            # else:
            #     raise ValueError(f"Invalid response from Privy API: {result}")
            
        except Exception as e:
            logger.error(f"Error signing transaction: {str(e)}")
            raise
    
    def send_transaction(self, transaction: TxParams) -> HexStr:
        """Send a transaction"""
        if not self._wallet_data:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        wallet_id = self._wallet_data.get('id')
        
        # Prepare transaction
        prepared_tx = self._prepare_transaction(transaction)
        
        # Generate idempotency key based on transaction params
        idempotency_key = f"tx-{wallet_id}-{prepared_tx.get('nonce', '')}-{uuid.uuid4()}"
        
        try:
            url = f"{self.base_url}/wallets/{wallet_id}/rpc"
            headers = self._get_auth_headers()
            
            # Get chain ID in CAIP2 format
            chain_id = 10143  # Monad testnet chain ID
            caip2 = f"eip155:{chain_id}"
            
            # Format the payload according to Privy API requirements
            payload = {
                "method": "eth_sendTransaction",
                "caip2": caip2,  # Added the required caip2 field
                "params": {
                    "transaction": prepared_tx  # CHANGED: Nested under params.transaction
                },
                "idempotency_key": idempotency_key
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            # Check for HTTP errors
            if response.status_code != 200:
                raise Exception(f"Error sending transaction: {response.status_code} {response.text}")
            
            result = response.json()
            
            # Check if response contains expected data
            if "data" in result:
                if "transactionHash" in result["data"]:
                    return result["data"]["transactionHash"]
                elif "hash" in result["data"]:
                    return result["data"]["hash"]
                else:
                    raise ValueError(f"Transaction hash not found in Privy API response: {result}")
            else:
                raise ValueError(f"Invalid response from Privy API: {result}")
            
        except Exception as e:
            logger.error(f"Error sending transaction: {str(e)}")
            raise
    
    def read_contract(
        self,
        contract_address: ChecksumAddress,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: Optional[List[Any]] = None,
        block_identifier: BlockIdentifier = "latest",
    ) -> Any:
        """Read data from a smart contract"""
        if not args:
            args = []
            
        contract = self._web3.eth.contract(address=contract_address, abi=abi)
        func = contract.functions[function_name]
        return func(*args).call(block_identifier=block_identifier)
    
    def wait_for_transaction_receipt(
        self, tx_hash: HexStr, timeout: float = 120, poll_latency: float = 0.1
    ) -> Dict[str, Any]:
        """Wait for transaction confirmation"""
        return self._web3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=timeout, poll_latency=poll_latency
        )
    
    def export_wallet(self) -> Dict[str, Any]:
        """Export wallet data for persistence"""
        if not self._wallet_data:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        class WalletData:
            def __init__(self, data):
                self.data = data
            
            def to_dict(self):
                return self.data
        
        # Format wallet data for AgentKit compatibility
        exported_data = {
            "walletId": self._wallet_data.get("id", ""),
            "address": self._wallet_data.get("address", ""),
            "networkId": self.config.network_id,
            "chainType": self._wallet_data.get("chain_type", "ethereum")
        }
        
        return WalletData(exported_data)
    
    async def get_transaction_status(self, transaction_hash: str) -> Dict[str, Any]:
        """Get transaction status from Privy"""
        if not self._wallet_data:
            raise ValueError("No wallet initialized. Call get_or_create_wallet first.")
        
        wallet_id = self._wallet_data.get('id')
        
        try:
            url = f"{self.base_url}/wallets/{wallet_id}/transactions/{transaction_hash}"
            headers = self._get_auth_headers()
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting transaction status: {str(e)}")
            raise
    
    def _prepare_transaction(self, transaction: TxParams) -> Dict[str, Any]:
        """Prepare transaction for signing/sending"""
        # Convert transaction to format expected by Privy API
        prepared_tx = dict(transaction)
        
        # Ensure 'to' is a checksum address
        if prepared_tx.get('to'):
            prepared_tx['to'] = Web3.to_checksum_address(prepared_tx['to'])
        
        # Set 'from' address if not present
        if 'from' not in prepared_tx:
            prepared_tx['from'] = self._address
        
        # Set value to zero if not present
        if 'value' not in prepared_tx:
            prepared_tx['value'] = 0
        
        # Set chain ID if not present
        if 'chainId' not in prepared_tx:
            prepared_tx['chainId'] = self._network.chain_id
        
        # Set nonce if not present
        if 'nonce' not in prepared_tx:
            prepared_tx['nonce'] = self._web3.eth.get_transaction_count(self._address)
        
        # Set gas parameters if not present
        if 'gas' not in prepared_tx:
            # Estimate gas
            gas_estimate = self._web3.eth.estimate_gas({
                'from': prepared_tx['from'],
                'to': prepared_tx.get('to', ''),
                'value': prepared_tx.get('value', 0),
                'data': prepared_tx.get('data', b'')
            })
            prepared_tx['gas'] = int(gas_estimate * self._gas_limit_multiplier)
        
        # For EIP-1559 transactions
        if 'maxFeePerGas' not in prepared_tx or 'maxPriorityFeePerGas' not in prepared_tx:
            max_priority_fee_per_gas, max_fee_per_gas = self._estimate_fees()
            prepared_tx['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            prepared_tx['maxFeePerGas'] = max_fee_per_gas
            prepared_tx['type'] = 2  # Set transaction type to EIP-1559

        # Convert bytes to hex strings for JSON serialization
        if 'data' in prepared_tx and isinstance(prepared_tx['data'], bytes):
            prepared_tx['data'] = '0x' + prepared_tx['data'].hex()
            
        return prepared_tx
    
    def _estimate_fees(self):
        """Estimate gas fees for a transaction"""
        def get_base_fee():
            latest_block = self._web3.eth.get_block("latest")
            base_fee = latest_block["baseFeePerGas"]
            return int(base_fee * self._fee_per_gas_multiplier)

        def get_max_priority_fee():
            max_priority_fee_per_gas = Web3.to_wei(0.1, "gwei")
            return int(max_priority_fee_per_gas * self._fee_per_gas_multiplier)

        base_fee_per_gas = get_base_fee()
        max_priority_fee_per_gas = get_max_priority_fee()
        max_fee_per_gas = base_fee_per_gas + max_priority_fee_per_gas

        return (max_priority_fee_per_gas, max_fee_per_gas)

# Helper functions to maintain compatibility with the existing codebase
def get_wallet_provider() -> PrivyWalletProvider:
    """Get the wallet provider instance"""
    return PrivyWalletProvider.get_instance()

def get_wallet_address(wallet_provider: Optional[PrivyWalletProvider] = None) -> str:
    """Get the wallet address from the provider"""
    if not wallet_provider:
        wallet_provider = get_wallet_provider()
    return wallet_provider.get_address()

def get_network_id(wallet_provider: Optional[PrivyWalletProvider] = None) -> str:
    """Get the network ID from the provider"""
    if not wallet_provider:
        wallet_provider = get_wallet_provider()
    return wallet_provider.get_network().network_id