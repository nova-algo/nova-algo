import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from src.api.drift.api import DriftAPI 
from solana.rpc.async_api import AsyncClient
from driftpy.drift_client import DriftClient
from driftpy.accounts.bulk_account_loader import BulkAccountLoader
from anchorpy import Wallet
import json
import os
from driftpy.types import (
    MarketType, OrderType, OrderParams, PositionDirection,
    PerpPosition, SpotPosition, UserAccount, Order, ModifyOrderParams
)

from solders.pubkey import Pubkey # type: ignore
from solders.keypair import Keypair # type: ignore
from driftpy.drift_client import DriftClient
from unittest.mock import call

from driftpy.account_subscription_config import AccountSubscriptionConfig

@pytest.fixture
def mock_drift_client():
    return AsyncMock(spec=DriftClient)

@pytest.fixture
def drift_api(mock_drift_client):
    api = DriftAPI("polling")
    api.drift_client = mock_drift_client
    return api

@pytest.fixture
def mock_keypair():
    return MagicMock(spec=Keypair)

@pytest.fixture
def mock_async_client():
    return AsyncMock()

@pytest.mark.asyncio
async def test_initialize(drift_api, mock_drift_client, mock_keypair, mock_async_client):
    mock_secret = [1, 2, 3, 4, 5]  # Example list of integers
    mock_keypair = MagicMock(spec=Keypair)
    mock_async_client = MagicMock(spec=AsyncClient)
    mock_drift_client = MagicMock(spec=DriftClient)
    mock_bulk_account_loader = MagicMock(spec=BulkAccountLoader)
    mock_open = MagicMock()

    with patch('src.api.drift.api.load_dotenv'), \
         patch('os.getenv', side_effect=['mock_keypath', 'mock_url']), \
         patch('src.api.drift.api.open', mock_open), \
         patch('json.load', return_value=mock_secret) as mock_json_load, \
         patch('src.api.drift.api.Keypair.from_bytes', return_value=mock_keypair), \
         patch('src.api.drift.api.Wallet', return_value=MagicMock(spec=Wallet)), \
         patch('src.api.drift.api.AsyncClient', return_value=mock_async_client), \
         patch('src.api.drift.api.BulkAccountLoader', return_value=mock_bulk_account_loader), \
         patch('src.api.drift.api.DriftClient', return_value=mock_drift_client), \
         patch('src.api.drift.api.logger.info') as mock_logger:

        await drift_api.initialize()

        # Assert that environment variables were checked
        os.getenv.assert_any_call("DRIFT_WALLET_PRIVATE_KEY")
        os.getenv.assert_any_call("RPC_URL")

        # Assert that the file was opened and read
        mock_open.assert_called_once()
        mock_json_load.assert_called_once()

        mock_drift_client.initialize_user.assert_called_once()
        assert drift_api.drift_client == mock_drift_client

    # You might want to add more assertions here to verify other aspects of initialization

@pytest.mark.asyncio
async def test_cancel_orders_for_market(drift_api, mock_drift_client):
    mock_user = MagicMock()
    mock_user.get_open_orders.return_value = [
        MagicMock(market_type=MarketType.Perp(), market_index=1),
        MagicMock(market_type=MarketType.Perp(), market_index=2),
        MagicMock(market_type=MarketType.Spot(), market_index=1),
    ]
    mock_drift_client.get_user.return_value = mock_user

    await drift_api.cancel_orders_for_market(MarketType.Perp(), 1)

    mock_drift_client.cancel_orders.assert_called_once_with(MarketType.Perp(), 1, sub_account_id=None)

@pytest.mark.asyncio
async def test_cancel_orders_for_market_and_direction(drift_api, mock_drift_client):
    mock_user = MagicMock()
    mock_user.get_open_orders.return_value = [
        MagicMock(market_type=MarketType.Perp(), market_index=1, direction=PositionDirection.Long()),
        MagicMock(market_type=MarketType.Perp(), market_index=1, direction=PositionDirection.Short()),
    ]
    mock_drift_client.get_user.return_value = mock_user

    await drift_api.cancel_orders_for_market_and_direction(MarketType.Perp(), 1, PositionDirection.Long())

    mock_drift_client.cancel_orders.assert_called_once_with(MarketType.Perp(), 1, PositionDirection.Long(), sub_account_id=None)

@pytest.mark.asyncio
async def test_cancel_all_orders(drift_api, mock_drift_client):
    mock_user = MagicMock()
    mock_user.get_open_orders.return_value = [
        MagicMock(market_type=MarketType.Perp(), market_index=1),
        MagicMock(market_type=MarketType.Spot(), market_index=2),
    ]
    mock_drift_client.get_user.return_value = mock_user

    await drift_api.cancel_all_orders()

    mock_drift_client.cancel_orders.assert_called_once_with(sub_account_id=None)

@pytest.mark.asyncio
async def test_place_limit_order_perp(drift_api, mock_drift_client):
    order_params = OrderParams(
        order_type=OrderType.Limit(),
        market_type=MarketType.Perp(),
        direction=PositionDirection.Long(),
        base_asset_amount=100,
        price=1000,
        market_index=1
    )

    await drift_api.place_limit_order(order_params)

    mock_drift_client.place_perp_order.assert_called_once_with(order_params)

@pytest.mark.asyncio
async def test_place_limit_order_spot(drift_api, mock_drift_client):
    order_params = OrderParams(
        order_type=OrderType.Limit(),
        market_type=MarketType.Spot(),
        direction=PositionDirection.Long(),
        base_asset_amount=100,
        price=1000,
        market_index=1
    )

    await drift_api.place_limit_order(order_params)

    mock_drift_client.place_spot_order.assert_called_once_with(order_params)

@pytest.mark.asyncio
async def test_place_limit_order_invalid_market_type(drift_api):
    order_params = OrderParams(
        order_type=OrderType.Limit(),
        market_type=MagicMock(),  # Invalid market type
        direction=PositionDirection.Long(),
        base_asset_amount=100,
        price=1000,
        market_index=1
    )

    with pytest.raises(ValueError):
        await drift_api.place_limit_order(order_params)

def test_get_position_perp(drift_api, mock_drift_client):
    mock_position = MagicMock(spec=PerpPosition)
    mock_drift_client.get_perp_position.return_value = mock_position

    position = drift_api.get_position(1, MarketType.Perp())

    assert position == mock_position
    mock_drift_client.get_perp_position.assert_called_once_with(1)

def test_get_position_spot(drift_api, mock_drift_client):
    mock_position = MagicMock(spec=SpotPosition)
    mock_drift_client.get_spot_position.return_value = mock_position

    position = drift_api.get_position(1, MarketType.Spot())

    assert position == mock_position
    mock_drift_client.get_spot_position.assert_called_once_with(1)

def test_get_user_account(drift_api, mock_drift_client):
    mock_user_account = MagicMock(spec=UserAccount)
    mock_drift_client.get_user_account.return_value = mock_user_account

    user_account = drift_api.get_user_account()

    assert user_account == mock_user_account
    assert drift_api.user_account == mock_user_account
    mock_drift_client.get_user_account.assert_called_once()

def test_get_open_orders(drift_api, mock_drift_client):
    mock_orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
    mock_user = MagicMock()
    mock_user.get_open_orders.return_value = mock_orders
    mock_drift_client.get_user.return_value = mock_user

    open_orders = drift_api.get_open_orders()

    assert open_orders == mock_orders
    mock_drift_client.get_user.assert_called_once()
    mock_user.get_open_orders.assert_called_once()

def test_get_market_index_and_type(drift_api, mock_drift_client):
    mock_drift_client.get_market_index_and_type.return_value = (1, MarketType.Perp())

    result = drift_api.get_market_index_and_type("SOL-PERP")

    assert result == (1, MarketType.Perp())
    mock_drift_client.get_market_index_and_type.assert_called_once_with("SOL-PERP")

@pytest.mark.asyncio
async def test_get_wallet_balance(drift_api, mock_drift_client):
    mock_drift_client.connection.get_balance.return_value = MagicMock(value=1000000)
    mock_drift_client.wallet.public_key = MagicMock()

    balance = await drift_api.get_wallet_balance()

    assert balance == 1000000
    mock_drift_client.connection.get_balance.assert_called_once_with(mock_drift_client.wallet.public_key)

@pytest.mark.asyncio
async def test_close_position_perp(drift_api, mock_drift_client):
    mock_position = MagicMock(spec=PerpPosition)
    mock_position.base_asset_amount = 100
    drift_api.get_position = AsyncMock(return_value=mock_position)
    mock_drift_client.convert_to_perp_precision.return_value = 100

    await drift_api.close_position(1, MarketType.Perp())

    mock_drift_client.place_perp_order.assert_called_once()
    args, _ = mock_drift_client.place_perp_order.call_args
    assert args[0].order_type == OrderType.Market()
    assert args[0].direction == PositionDirection.Short()
    assert args[0].base_asset_amount == 100
    assert args[0].reduce_only == True


@pytest.mark.asyncio
async def test_close_position_spot(drift_api, mock_drift_client):
    mock_position = MagicMock(spec=SpotPosition)
    mock_position.scaled_balance = 100
    drift_api.get_position = AsyncMock(return_value=mock_position)

    # Update this part to match the perp test
    mock_drift_client.convert_to_spot_precision.return_value = 100

    await drift_api.close_position(1, MarketType.Spot())

    mock_drift_client.place_spot_order.assert_called_once()
    args, _ = mock_drift_client.place_spot_order.call_args
    
    # Print the entire OrderParams object for debugging
    print(f"OrderParams: {args[0]}")
    
    assert args[0].order_type == OrderType.Market()
    assert args[0].direction == PositionDirection.Short()
    assert args[0].base_asset_amount == 100
    # Note: We don't assert reduce_only for spot orders as it's not applicable

    # Add this assertion to ensure the conversion method was called
    mock_drift_client.convert_to_spot_precision.assert_called_once_with(100)

@pytest.mark.asyncio
async def test_close_position_no_position(drift_api):
    drift_api.get_position = AsyncMock(return_value=None)

    result, message = await drift_api.close_position(1, MarketType.Perp())

    assert result is None
    assert "No position found" in message

@pytest.mark.asyncio
async def test_cancel_order(drift_api, mock_drift_client):
    mock_drift_client.cancel_order.return_value = "tx_signature"

    result = await drift_api.cancel_order(order_id=1, sub_account_id=0)

    assert result["success"] == True
    assert result["transaction_signature"] == "tx_signature"
    mock_drift_client.cancel_order.assert_called_once_with(1, 0)

@pytest.mark.asyncio
async def test_cancel_order_exception(drift_api, mock_drift_client):
    mock_drift_client.cancel_order.side_effect = Exception("Test error")

    result = await drift_api.cancel_order(order_id=1)

    assert result["success"] == False
    assert "Test error" in result["message"]

@pytest.mark.asyncio
async def test_modify_order(drift_api, mock_drift_client):
    mock_user = MagicMock()
    mock_order = MagicMock(
        price=1000,
        base_asset_amount=100,
        market_type=MarketType.Perp(),
        direction=PositionDirection.Long(),
        market_index=1,
        reduce_only=False,
        post_only=False,
        order_type=OrderType.Limit()
    )
    mock_user.get_order.return_value = mock_order
    mock_drift_client.get_user.return_value = mock_user
    mock_drift_client.modify_order.return_value = "tx_signature"

    result = await drift_api.modify_order(order_id=1, new_price=1100, new_size=110)

    assert result["success"] == True
    assert result["transaction_signature"] == "tx_signature"
    mock_drift_client.modify_order.assert_called_once()
    args, _ = mock_drift_client.modify_order.call_args
    assert args[0].price == 1100
    assert args[0].base_asset_amount == 110

@pytest.mark.asyncio
async def test_modify_order_not_found(drift_api, mock_drift_client):
    mock_user = MagicMock()
    mock_user.get_order.return_value = None
    mock_drift_client.get_user.return_value = mock_user

    result = await drift_api.modify_order(order_id=1, new_price=1100)

    assert result["success"] == False
    assert "Order with ID 1 not found" in result["message"]

def test_get_perp_position(drift_api, mock_drift_client):
    mock_user = MagicMock()
    mock_position = MagicMock(spec=PerpPosition)
    mock_user.get_perp_position.return_value = mock_position
    mock_drift_client.get_user.return_value = mock_user

    position = drift_api.get_perp_position(1)

    assert position == mock_position
    mock_drift_client.get_user.assert_called_once_with(None)
    mock_user.get_perp_position.assert_called_once_with(1)

def test_get_spot_position(drift_api, mock_drift_client):
    mock_user = MagicMock()
    mock_position = MagicMock(spec=SpotPosition)
    mock_user.get_spot_position.return_value = mock_position
    mock_drift_client.get_user.return_value = mock_user

    position = drift_api.get_spot_position(1)

    assert position == mock_position
    mock_drift_client.get_user.assert_called_once_with(None)
    mock_user.get_spot_position.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_get_all_open_positions(drift_api, mock_drift_client):
    mock_drift_client.sub_account_ids = [1, 2]
    drift_api.get_open_perp_positions = AsyncMock(return_value=([MagicMock(spec=PerpPosition)], None))
    drift_api.get_open_spot_positions = AsyncMock(return_value=([MagicMock(spec=SpotPosition)], None))

    positions, error = await drift_api.get_all_open_positions()

    assert error is None
    assert len(positions) == 3  # Main account (0) and two sub-accounts
    assert all('perp' in account and 'spot' in account for account in positions.values())
    assert drift_api.get_open_perp_positions.call_count == 3
    assert drift_api.get_open_spot_positions.call_count == 3

@pytest.mark.asyncio
async def test_get_all_open_positions_with_errors(drift_api, mock_drift_client):
    mock_drift_client.sub_account_ids = [1]
    drift_api.get_open_perp_positions = AsyncMock(side_effect=[
        ([MagicMock(spec=PerpPosition)], None),
        ([], "Perp error")
    ])
    drift_api.get_open_spot_positions = AsyncMock(side_effect=[
        ([MagicMock(spec=SpotPosition)], None),
        ([], "Spot error")
    ])

    positions, error = await drift_api.get_all_open_positions()

    assert error is None
    assert len(positions) == 1  # Only main account (0) has positions
    assert 'perp' in positions[0] and 'spot' in positions[0]
    assert drift_api.get_open_perp_positions.call_count == 2
    assert drift_api.get_open_spot_positions.call_count == 2

@pytest.mark.asyncio
async def test_get_all_open_positions_no_positions(drift_api, mock_drift_client):
    mock_drift_client.sub_account_ids = []
    drift_api.get_open_perp_positions = AsyncMock(return_value=([], None))
    drift_api.get_open_spot_positions = AsyncMock(return_value=([], None))

    positions, error = await drift_api.get_all_open_positions()

    assert error == "Failed to retrieve any open positions"
    assert positions == {}
    assert drift_api.get_open_perp_positions.call_count == 1
    assert drift_api.get_open_spot_positions.call_count == 1

@pytest.mark.asyncio
async def test_place_limit_order_client_exception(drift_api, mock_drift_client):
    mock_drift_client.place_perp_order.side_effect = Exception("Drift client error")
    order_params = OrderParams(
        order_type=OrderType.Limit(),
        market_type=MarketType.Perp(),
        direction=PositionDirection.Long(),
        base_asset_amount=100,
        price=1000,
        market_index=1
    )

    with pytest.raises(Exception, match="Drift client error"):
        await drift_api.place_limit_order(order_params)

@pytest.mark.asyncio
async def test_close_position_invalid_market_type(drift_api):
    with pytest.raises(ValueError, match="Invalid market type"):
        await drift_api.close_position(1, MagicMock())  # Invalid market type

@pytest.mark.asyncio
async def test_get_all_open_positions_subaccount_error(drift_api, mock_drift_client):
    mock_drift_client.sub_account_ids = [1]
    drift_api.get_open_perp_positions = AsyncMock(side_effect=Exception("Subaccount error"))
    drift_api.get_open_spot_positions = AsyncMock(return_value=([], None))

    positions, error = await drift_api.get_all_open_positions()

    assert error == "Failed to retrieve any open positions"
    assert positions == {}

def test_get_perp_position_exception(drift_api, mock_drift_client):
    mock_drift_client.get_user.side_effect = Exception("User retrieval error")

    position = drift_api.get_perp_position(1)

    assert position is None

def test_get_spot_position_exception(drift_api, mock_drift_client):
    mock_drift_client.get_user.side_effect = Exception("User retrieval error")

    position = drift_api.get_spot_position(1)

    assert position is None

@pytest.mark.asyncio
async def test_modify_order_invalid_inputs(drift_api):
    result = await drift_api.modify_order(order_id=None)

    assert result["success"] == False
    assert "Invalid order ID" in result["message"]

@pytest.mark.asyncio
async def test_cancel_order_invalid_inputs(drift_api):
    result = await drift_api.cancel_order(order_id=None)

    assert result["success"] == False
    assert "Invalid order ID" in result["message"]