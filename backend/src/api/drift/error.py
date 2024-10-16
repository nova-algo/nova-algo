from enum import Enum 


class DriftAPIRequestError(Exception): 
    """ 
    Exeception thrown when Drift request via websocket fails. 
    
    Parameters 
    ---------- 
    response: dict 
        Error response received from Drift.
    """
    def __init__(self, response: str) -> None: 
        self.message = response["error"]["message"]
        self.status_code = response["error"]["code"]
        self.code = self.status_code
        
        
class ErrorStatus(Enum):
    RETRY = {
        6001: "InvalidInsuranceFundAuthority",
        6020: "BnConversionError",
        6021: "ClockUnavailable",
        6022: "UnableToLoadOracle",
        6035: "InvalidOracle",
        6036: "OracleNotFound",
        6065: "UnableToLoadAccountLoader",
        6077: "CouldNotLoadMarketData",
        6080: "UnableToLoadPerpMarketAccount",
        6082: "UnableToCastUnixTime",
        6086: "CouldNotLoadSpotMarketData",
        6089: "UnableToLoadSpotMarketAccount",
        6096: "AMMNotUpdatedInSameSlot",
        6103: "CouldNotDeserializeMaker",
        6104: "CouldNotDeserializeMakerStats",
        6141: "FailedSerumCPI",
        6142: "FailedToFillOnExternalMarket",
        6202: "BlockchainClockInconsistency",
        6219: "UnableToGetLimitPrice",
        6228: "CouldNotLoadUserData",
        6231: "CouldNotLoadUserStatsData",
        6235: "UnableToLoadUserAccount",
        6237: "UnableToLoadUserStatsAccount",
        6242: "FailedToGetMint",
        6243: "FailedPhoenixCPI",
        6244: "FailedToDeserializePhoenixMarket",
    },
    
    IGNORE = {
        6004: "SufficientCollateral",
        6012: "InvalidRepegRedundant",
        6038: "MaxDeposit",
        6062: "OrderNotOpen",
        6072: "NoPositionsLiquidatable",
        6073: "InvalidMarginRatio",
        6076: "CantExpireOrders",
        6097: "AuctionNotComplete",
        6111: "OrderNotTriggerable",
        6114: "PositionDoesntHaveOpenPositionOrOrders",
        6115: "AllOrdersAreAlreadyLiquidations",
        6116: "CantCancelLiquidationOrder",
        6126: "UserNotBankrupt",
        6183: "MaxIFWithdrawReached",
        6184: "NoIFWithdrawAvailable",
        6199: "NoIFWithdrawRequestInProgress",
        6200: "IFWithdrawRequestTooSmall",
        6204: "NewLPSizeTooSmall",
        6238: "UserNotInactive",
    },
    
    CANCEL = {
        6002: "InsufficientDeposit",
        6003: "InsufficientCollateral",
        6005: "MaxNumberOfPositions",
        6007: "MarketDelisted",
        6010: "UserHasNoPositionInMarket",
        6015: "SlippageOutsideLimit",
        6016: "OrderSizeTooSmall",
        6023: "PriceBandsBreached",
        6024: "ExchangePaused",
        6037: "LiquidationsBlockedByOracle",
        6057: "PlacePostOnlyLimitFailure",
        6058: "UserHasNoOrder",
        6059: "OrderAmountTooSmall",
        6060: "MaxNumberOfOrders",
        6061: "OrderDoesNotExist",
        6064: "ReduceOnlyOrderIncreasedRisk",
        6066: "TradeSizeTooLarge",
        6070: "CouldNotDeserializeReferrerStats",
        6071: "UserOrderIdAlreadyInUse",
        6074: "CantCancelPostOnlyOrder",
        6075: "InvalidOracleOffset",
        6083: "CouldNotFindSpotPosition",
        6084: "NoSpotPositionAvailable",
        6090: "SpotMarketWrongMutability",
        6091: "SpotMarketInterestNotUpToDate",
        6095: "InsufficientCollateralForSettlingPNL",
        6098: "MakerNotFound",
        6099: "MakerStatsNotFound",
        6102: "MakerOrderNotFound",
        6105: "AuctionPriceDoesNotSatisfyMaker",
        6106: "MakerCantFulfillOwnOrder",
        6107: "MakerOrderMustBePostOnly",
        6108: "CantMatchTwoPostOnlys",
        6109: "OrderBreachesOraclePriceLimits",
        6110: "OrderMustBeTriggeredFirst",
        6112: "OrderDidNotSatisfyTriggerCondition",
        6117: "UserIsBeingLiquidated",
        6118: "LiquidationsOngoing",
        6119: "WrongSpotBalanceType",
        6120: "UserCantLiquidateThemself",
        6121: "InvalidPerpPositionToLiquidate",
        6122: "InvalidBaseAssetAmountForLiquidatePerp",
        6123: "InvalidPositionLastFundingRate",
        6124: "InvalidPositionDelta",
        6128: "DailyWithdrawLimit",
        6130: "InsufficientLPTokens",
        6131: "CantLPWithPerpPosition",
        6132: "UnableToBurnLPTokens",
        6133: "TryingToRemoveLiquidityTooFast",
        6146: "MarketActionPaused",
        6147: "MarketPlaceOrderPaused",
        6148: "MarketFillOrderPaused",
        6149: "MarketWithdrawPaused",
        6150: "ProtectedAssetTierViolation",
        6151: "IsolatedAssetTierViolation",
        6153: "ReduceOnlyWithdrawIncreasedRisk",
        6154: "MaxOpenInterest",
        6156: "LiquidationDoesntSatisfyLimitPrice",
        6157: "MarginTradingDisabled",
        6171: "InvalidOrderFillPrice",
        6205: "MarketStatusInvalidForNewLP",
        6206: "InvalidMarkTwapUpdateDetected",
        6212: "SpotOrdersDisabled",
        6213: "MarketBeingInitialized",
        6215: "InvalidTriggerOrderCondition",
        6220: "InvalidLiquidation",
        6221: "SpotFulfillmentConfigDisabled",
        6226: "MarginOrdersOpen",
        6227: "TierViolationLiquidatingPerpPnl",
        6239: "RevertFill",
    },
    
    BLOCK = {
        6000: "InvalidSpotMarketAuthority",
        6006: "AdminControlsPricesDisabled",
        6008: "MarketIndexAlreadyInitialized",
        6009: "UserAccountAndUserPositionsAccountMismatch",
        6011: "InvalidInitialPeg",
        6013: "InvalidRepegDirection",
        6014: "InvalidRepegProfitability",
        6017: "InvalidUpdateK",
        6018: "AdminWithdrawTooLarge",
        6019: "MathError",
        6025: "InvalidWhitelistToken",
        6026: "WhitelistTokenNotFound",
        6027: "InvalidDiscountToken",
        6028: "DiscountTokenNotFound",
        6029: "ReferrerNotFound",
        6030: "ReferrerStatsNotFound",
        6031: "ReferrerMustBeWritable",
        6032: "ReferrerStatsMustBeWritable",
        6033: "ReferrerAndReferrerStatsAuthorityUnequal",
        6034: "InvalidReferrer",
        6039: "CantDeleteUserWithCollateral",
        6040: "InvalidFundingProfitability",
        6041: "CastingFailure",
        6042: "InvalidOrder",
        6043: "InvalidOrderMaxTs",
        6044: "InvalidOrderMarketType",
        6045: "InvalidOrderForInitialMarginReq",
        6046: "InvalidOrderNotRiskReducing",
        6047: "InvalidOrderSizeTooSmall",
        6049: "InvalidOrderBaseQuoteAsset",
        6050: "InvalidOrderIOC",
        6051: "InvalidOrderPostOnly",
        6052: "InvalidOrderIOCPostOnly",
        6053: "InvalidOrderTrigger",
        6054: "InvalidOrderAuction",
        6055: "InvalidOrderOracleOffset",
        6056: "InvalidOrderMinOrderSize",
        6063: "FillOrderDidNotUpdateState",
        6067: "UserCantReferThemselves",
        6068: "DidNotReceiveExpectedReferrer",
        6069: "CouldNotDeserializeReferrer",
        6078: "PerpMarketNotFound",
        6079: "InvalidMarketAccount",
        6081: "MarketWrongMutability",
        6085: "InvalidSpotMarketInitialization",
        6087: "SpotMarketNotFound",
        6088: "InvalidSpotMarketAccount",
        6093: "UserMustSettleTheirOwnPositiveUnsettledPNL",
        6094: "CantUpdatePoolBalanceType",
        6100: "MakerMustBeWritable",
        6101: "MakerStatsMustBeWritable",
        6113: "PositionAlreadyBeingLiquidated",
        6125: "UserBankrupt",
        6127: "UserHasInvalidBorrow",
        6129: "DefaultError",
        6134: "InvalidSpotMarketVault",
        6135: "InvalidSpotMarketState",
        6136: "InvalidSerumProgram",
        6137: "InvalidSerumMarket",
        6138: "InvalidSerumBids",
        6139: "InvalidSerumAsks",
        6140: "InvalidSerumOpenOrders",
        6143: "InvalidFulfillmentConfig",
        6144: "InvalidFeeStructure",
        6145: "InsufficientIFShares",
        6152: "UserCantBeDeleted",
        6155: "CantResolvePerpBankruptcy",
        6158: "InvalidMarketStatusToSettlePnl",
        6159: "PerpMarketNotInSettlement",
        6160: "PerpMarketNotInReduceOnly",
        6161: "PerpMarketSettlementBufferNotReached",
        6162: "PerpMarketSettlementUserHasOpenOrders",
        6163: "PerpMarketSettlementUserHasActiveLP",
        6164: "UnableToSettleExpiredUserPosition",
        6165: "UnequalMarketIndexForSpotTransfer",
        6166: "InvalidPerpPositionDetected",
        6167: "InvalidSpotPositionDetected",
        6168: "InvalidAmmDetected",
        6170: "InvalidAmmLimitPriceOverride",
        6172: "SpotMarketBalanceInvariantViolated",
        6173: "SpotMarketVaultInvariantViolated",
        6174: "InvalidPDA",
        6175: "InvalidPDASigner",
        6176: "RevenueSettingsCannotSettleToIF",
        6177: "NoRevenueToSettleToIF",
        6178: "NoAmmPerpPnlDeficit",
        6179: "SufficientPerpPnlPool",
        6180: "InsufficientPerpPnlPool",
        6181: "PerpPnlDeficitBelowThreshold",
        6182: "MaxRevenueWithdrawPerPeriodReached",
        6185: "InvalidIFUnstake",
        6186: "InvalidIFUnstakeSize",
        6187: "InvalidIFUnstakeCancel",
        6188: "InvalidIFForNewStakes",
        6189: "InvalidIFRebase",
        6190: "InvalidInsuranceUnstakeSize",
        6191: "InvalidOrderLimitPrice",
        6192: "InvalidIFDetected",
        6193: "InvalidAmmMaxSpreadDetected",
        6194: "InvalidConcentrationCoef",
        6195: "InvalidSrmVault",
        6196: "InvalidVaultOwner",
        6197: "InvalidMarketStatusForFills",
        6198: "IFWithdrawRequestInProgress",
        6201: "IncorrectSpotMarketAccountPassed",
        6203: "InvalidIFSharesDetected",
        6207: "MarketSettlementAttemptOnActiveMarket",
        6208: "MarketSettlementRequiresSettledLP",
        6209: "MarketSettlementAttemptTooEarly",
        6210: "MarketSettlementTargetPriceInvalid",
        6211: "UnsupportedSpotMarket",
        6214: "InvalidUserSubAccountId",
        6216: "InvalidSpotPosition",
        6217: "CantTransferBetweenSameUserAccount",
        6218: "InvalidPerpPosition",
        6222: "InvalidMaker",
        6223: "FailedUnwrap",
        6224: "MaxNumberOfUsers",
        6225: "InvalidOracleForSettlePnl",
        6229: "UserWrongMutability",
        6230: "InvalidUserAccount",
        6232: "UserStatsWrongMutability",
        6233: "InvalidUserStatsAccount",
        6234: "UserNotFound",
        6236: "UserStatsNotFound",
        6240: "InvalidMarketAccountforDeletion",
        6241: "InvalidSpotFulfillmentParams",
        6245: "InvalidPricePrecision",
        6246: "InvalidPhoenixProgram",
        6247: "InvalidPhoenixMarket",
    }
    
    def error_status(error):
        error_number = error["error"]["code"]
        for status in ErrorStatus:
            if error_number in status.value:
                return status.name
    