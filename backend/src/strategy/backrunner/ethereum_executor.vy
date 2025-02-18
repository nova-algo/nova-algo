# #pragma version >=0.3.10

# from vyper.interfaces import ERC20 as IERC20

# interface IWETH:    
#     def deposit(): payable

# interface IUniswapV3Pool:
#     def factory() -> address: view
#     def fee() -> uint24: view
#     def tickSpacing() -> int24: view
#     def token0() -> address: view
#     def token1() -> address: view
#     def swap(
#         recipient: address, 
#         zeroForOne: bool, 
#         amountSpecified: int256, 
#         sqrtPriceLimitX96: uint160, 
#         data: Bytes[32]
#         ) -> (int256, int256): nonpayable

# OWNER_ADDR: immutable(address)
# WETH_ADDR: constant(address) = (
#     0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
# )
# V3_POOL_INIT_CODE_HASH: constant(bytes32) = (
#     0xe34f199b19b2b4f47f68442619d555527d244f78a3297ea89325f843f87b8b54
# )
# MAX_PAYLOADS: constant(uint256) = 16
# MAX_PAYLOAD_BYTES: constant(uint256) = 1024

# struct payload:
#     target: address
#     calldata: Bytes[MAX_PAYLOAD_BYTES]
#     value: uint256


# @external
# @payable
# def __init__():
#     OWNER_ADDR = msg.sender

#     # Wrap initial Ether to WETH
#     if msg.value > 0:
#         IWETH(WETH_ADDR).deposit(value=msg.value)


# @external
# @payable
# def execute_payloads(
#     payloads: DynArray[payload, MAX_PAYLOADS],
#     balance_check: bool = True,
#     bribe_bips: uint256 = 0
# ):
#     assert msg.sender == OWNER_ADDR, "!OWNER"

#     weth_balance_before: uint256 = empty(uint256)
#     weth_balance_after: uint256 = empty(uint256)   

#     if balance_check:        
#         weth_balance_before = IERC20(WETH_ADDR).balanceOf(self)

#     for _payload in payloads:
#         raw_call(
#             _payload.target,
#             _payload.calldata,
#             value=_payload.value,
#         )

#     if balance_check:
#         weth_balance_after = IERC20(WETH_ADDR).balanceOf(self)
#         assert weth_balance_after > weth_balance_before, "WETH BALANCE REDUCTION"

#         # For a 1% bribe set = 100 bips
#         # For a 10% bribe set = 1_000 bips
#         # For a 100% bribe set = 10_000 bips

#         if bribe_bips > 0:            
#             send(
#                 block.coinbase,
#                 min(
#                     msg.value,
#                     bribe_bips * (
#                         weth_balance_after - weth_balance_before
#                     ) / 10_000,
#                 )
#             )


# @external
# @payable
# def uniswapV3SwapCallback(
#     amount0_delta: int256,
#     amount1_delta: int256,
#     data: Bytes[32]
# ):
#     # reject callbacks that did not originate from the owner's EOA
#     assert tx.origin == OWNER_ADDR, "!OWNER"

#     # get the token0/token1 addresses and fee reported by msg.sender
#     factory: address = IUniswapV3Pool(msg.sender).factory()   
#     token0: address = IUniswapV3Pool(msg.sender).token0()
#     token1: address = IUniswapV3Pool(msg.sender).token1()
#     fee: uint24 = IUniswapV3Pool(msg.sender).fee()

#     assert msg.sender == convert(
#         slice(
#             keccak256(
#                 concat(
#                     0xFF,
#                     convert(factory,bytes20),
#                     keccak256(_abi_encode(token0, token1, fee)),
#                     V3_POOL_INIT_CODE_HASH,
#                 )
#             ),
#             12,
#             20,
#         ),
#         address
#     ), "INVALID V3 LP ADDRESS"

#     # repay token back to pool
#     if amount0_delta > 0:
#         IERC20(token0).transfer(
#             msg.sender,
#             convert(amount0_delta, uint256)
#         )
#     elif amount1_delta > 0:
#         IERC20(token1).transfer(
#             msg.sender,
#             convert(amount1_delta, uint256)
#         )
#     else:
#         raise "REJECTED 0 LIQUIDITY SWAP"


# @external
# @payable
# def __default__():
#     # accept basic Ether transfers to the contract with no calldata
#     if len(msg.data) == 0:
#         return
#     # revert on all other calls
#     else:
#         raise