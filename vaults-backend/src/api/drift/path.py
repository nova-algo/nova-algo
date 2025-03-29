from enum import Enum


class Listing(str, Enum):
    GET_TRADING_HISTORY = "user/${accountKey}/tradeRecords/${year}/${year}${month}${day}"
    GET_MARKET_TRADE_RECORDS = "market/${marketSymbol}/tradeRecords/${year}/${year}${month}${day}"
    GET_FUNDING_RATE_RECORDS = "market/${marketSymbol}/fundingRateRecords/${year}/${year}${month}${day}"
    GET_FUNDING_PAYMENTS_RECORDS = "user/${accountKey}/fundingPaymentRecords/${year}/${year}${month}${day}"
    USER_DEPOSIT_RECORDS = "user/${accountKey}/depositRecords/${year}/${year}${month}${day}" 
    GET_LIQUIDATIONS_RECORDS = "user/${accountKey}/liquidationRecords/${year}/${year}${month}${day}" 
    GET_SETTLE_PNL_RECORDS = "user/${accountKey}/settlePnlRecords/${year}/${year}${month}${day}" 
    GET_LP_RECORD = "user/${accountKey}/lpRecord/${year}/${year}${month}${day}" 
    
    def __str__(self) -> str:
        return self.value


class Matching_engine:
    PATHS = {
        "private/buy",
        "private/sell",
        "private/edit",
        "private/edit_by_label",
        "private/cancel",
        "private/cancel_by_label",
        "private/cancel_all",
        "private/cancel_all_by_instrument",
        "private/cancel_all_by_currency",
        "private/cancel_all_by_kind_or_type",
        "private/close_position",
        "private/verify_block_trade",
        "private/execute_block_trade",
        "private/move_positions",
        "private/mass_quote",
        "private/cancel_quotes",
    }
    