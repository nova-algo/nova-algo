# from enum import Enum

# class UniswapAPIRequestError(Exception):
#     """
#     Exception thrown when Uniswap request fails.
    
#     Parameters
#     ----------
#     response: dict
#         Error response received from Uniswap.
#     """
#     def __init__(self, response: dict) -> None:
#         self.message = response.get("error", {}).get("message", "Unknown error")
#         self.code = response.get("error", {}).get("code", -1)

# class ErrorStatus(Enum):
#     INSUFFICIENT_LIQUIDITY = "INSUFFICIENT_LIQUIDITY"
#     INSUFFICIENT_INPUT_AMOUNT = "INSUFFICIENT_INPUT_AMOUNT"
#     INSUFFICIENT_OUTPUT_AMOUNT = "INSUFFICIENT_OUTPUT_AMOUNT"
#     EXCESSIVE_SLIPPAGE = "EXCESSIVE_SLIPPAGE"
#     TRANSACTION_FAILED = "TRANSACTION_FAILED" 