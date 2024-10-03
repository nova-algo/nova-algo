import asyncio
from dotenv import load_dotenv
from src.api.drift.api import DriftAPI
from driftpy.types import OrderParams, MarketType, OrderType, PositionDirection, PostOnlyParams, Order
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION # type: ignore

async def run_drift_api_initialize():
    # Load environment variables from .env file
    load_dotenv()

    # Create DriftAPI instance
    drift_api = DriftAPI("devnet")

    try:
        # Run initialize method
        await drift_api.initialize(subscription_type="cached")
        
        print("Initialization successful!")
        print(f"Public key: {drift_api.drift_client.wallet.payer.pubkey()}")
        
        # Additional checks
        print(f"Connection established: {drift_api.connection is not None}")
        print(f"Drift client initialized: {drift_api.drift_client is not None}")

    except Exception as e:
        print(f"Initialization failed: {str(e)}")
    
    # finally:
    #     # Clean up resources
    #     if hasattr(drift_api, 'connection') and drift_api.connection:
    #         await drift_api.connection.close()

# if __name__ == "__main__":
#     asyncio.run(run_drift_api_initialize())

async def test_place_order():
    load_dotenv()
    drift_api = DriftAPI("devnet")

    try:
        await drift_api.initialize(subscription_type="cached")
        #await drift_api.drift_client.add_user(0)
    
        # order_params = OrderParams(
        #     market_index=0,  # Assuming BTC-PERP is at index 0
        #     market_type=MarketType.Perp(),
        #     order_type=OrderType.Limit(),
        #     direction=PositionDirection.Long(),
        #     base_asset_amount=int(0.001 * BASE_PRECISION),  # Convert to native units
        #     price=int(30000 * PRICE_PRECISION),  # Convert to native units
        #     reduce_only=False,
        #     post_only=True,
        # )

        order_params = OrderParams(
            market_type=MarketType.Perp(),
            order_type=OrderType.Limit(),
            base_asset_amount=drift_api.drift_client.convert_to_perp_precision(1),
            market_index=0,
            direction=PositionDirection.Long(),
            price=drift_api.drift_client.convert_to_price_precision(21.88),
            post_only=PostOnlyParams.TryPostOnly(),
        )

        await drift_api.place_order(order_params)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    # finally:
    #     if hasattr(drift_api, 'connection') and drift_api.connection:
    #         await drift_api.connection.close()

# if __name__ == "__main__":
#     asyncio.run(test_place_order())
#     #asyncio.run(run_drift_api_initialize())

async def test_get_open_orders():
    load_dotenv()
    drift_api = DriftAPI("devnet")

    try:
        await drift_api.initialize(subscription_type="cached")
        
        order_params = OrderParams(
            market_type=MarketType.Perp(),
            order_type=OrderType.Limit(),
            base_asset_amount=drift_api.drift_client.convert_to_perp_precision(0.01),
            #base_asset_amount=drift_api.drift_client.convert_to_spot_precision(0.01, 1),
            market_index=0,
            direction=PositionDirection.Long(),
            price=drift_api.drift_client.convert_to_price_precision(30000),
            post_only=PostOnlyParams.TryPostOnly(),
        )

        #await drift_api.place_order(order_params)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    await asyncio.sleep(5)  # Wait for 5 seconds
    try:
        #await drift_api.initialize(subscription_type="cached")
        
        #await drift_api.drift_client.get_user().subscribe()
        open_orders = drift_api.drift_client.get_user().get_user_account().open_orders
        print(f"open_orders: {open_orders}")
        
        print(f"Number of open orders: {len(open_orders)}")
        for order in open_orders:
            print(f"Order ID: {order.order_id}")
            print(f"Market Index: {order.market_index}")
            print(f"Market Type: {order.market_type}")
            print(f"Direction: {order.direction}")
            print(f"Base Asset Amount: {order.base_asset_amount}")
            print(f"Price: {order.price}")
            print("---")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    # finally:
    #     if hasattr(drift_api, 'connection') and drift_api.connection:
    #         await drift_api.connection.close()

if __name__ == "__main__":
    asyncio.run(test_get_open_orders())