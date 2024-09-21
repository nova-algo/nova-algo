class DriftAPIError(Exception):
    """Base exception class for DriftAPI errors."""
    pass

class InitializationError(DriftAPIError):
    """Raised when there's an error during API initialization."""
    pass

class WalletError(DriftAPIError):
    """Raised when there's an issue with the wallet or keypair."""
    pass

class ConnectionError(DriftAPIError):
    """Raised when there's an issue connecting to the Solana network."""
    pass

class OrderError(DriftAPIError):
    """Raised when there's an error placing or canceling orders."""
    pass

class PositionError(DriftAPIError):
    """Raised when there's an error related to position management."""
    pass

class MarketError(DriftAPIError):
    """Raised when there's an error related to market operations."""
    pass

class LeverageError(DriftAPIError):
    """Raised when there's an error setting or adjusting leverage."""
    pass

class KillSwitchError(DriftAPIError):
    """Raised when there's an error executing the kill switch."""
    pass

def handle_drift_api_error(func):
    """Decorator to handle DriftAPI errors."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except InitializationError as e:
            print(f"Initialization Error: {str(e)}")
        except WalletError as e:
            print(f"Wallet Error: {str(e)}")
        except ConnectionError as e:
            print(f"Connection Error: {str(e)}")
        except OrderError as e:
            print(f"Order Error: {str(e)}")
        except PositionError as e:
            print(f"Position Error: {str(e)}")
        except MarketError as e:
            print(f"Market Error: {str(e)}")
        except LeverageError as e:
            print(f"Leverage Error: {str(e)}")
        except KillSwitchError as e:
            print(f"Kill Switch Error: {str(e)}")
        except DriftAPIError as e:
            print(f"DriftAPI Error: {str(e)}")
        except Exception as e:
            print(f"Unexpected Error: {str(e)}")
    return wrapper