from enum import Enum
from typing import Optional

class UniswapAPIRequestError(Exception):
    """Exception thrown when Uniswap request fails"""
    def __init__(self, response: dict) -> None:
        self.message = response.get("error", {}).get("message", "Unknown error")
        self.code = response.get("error", {}).get("code", -1)
        super().__init__(self.message)

class ErrorStatus(Enum):
    INSUFFICIENT_LIQUIDITY = "INSUFFICIENT_LIQUIDITY"
    INSUFFICIENT_INPUT_AMOUNT = "INSUFFICIENT_INPUT_AMOUNT"
    INSUFFICIENT_OUTPUT_AMOUNT = "INSUFFICIENT_OUTPUT_AMOUNT"
    EXCESSIVE_SLIPPAGE = "EXCESSIVE_SLIPPAGE"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    
class UniswapError(Exception):
    """Base class for Uniswap errors"""
    def __init__(self, status: ErrorStatus, message: Optional[str] = None):
        self.status = status
        self.message = message or status.value
        super().__init__(self.message)

class InsufficientLiquidityError(UniswapError):
    def __init__(self, message: Optional[str] = None):
        super().__init__(ErrorStatus.INSUFFICIENT_LIQUIDITY, message)

class InsufficientInputAmountError(UniswapError):
    def __init__(self, message: Optional[str] = None):
        super().__init__(ErrorStatus.INSUFFICIENT_INPUT_AMOUNT, message)

class ExcessiveSlippageError(UniswapError):
    def __init__(self, message: Optional[str] = None):
        super().__init__(ErrorStatus.EXCESSIVE_SLIPPAGE, message) 