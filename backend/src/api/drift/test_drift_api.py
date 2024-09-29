import asyncio
from dotenv import load_dotenv
from src.api.drift.api import DriftAPI

async def run_drift_api_initialize():
    # Load environment variables from .env file
    load_dotenv()

    # Create DriftAPI instance
    drift_api = DriftAPI()

    try:
        # Run initialize method
        await drift_api.initialize(subscription_type="polling")
        
        print("Initialization successful!")
        print(f"Public key: {drift_api.drift_client.wallet.payer.pubkey()}")
        
        # Additional checks
        print(f"Connection established: {drift_api.connection is not None}")
        print(f"Drift client initialized: {drift_api.drift_client is not None}")

    except Exception as e:
        print(f"Initialization failed: {str(e)}")
    
    finally:
        # Clean up resources
        if hasattr(drift_api, 'connection') and drift_api.connection:
            await drift_api.connection.close()

if __name__ == "__main__":
    asyncio.run(run_drift_api_initialize())