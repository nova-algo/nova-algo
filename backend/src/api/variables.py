import logging
from collections import OrderedDict
from datetime import datetime, timezone

import requests

from src.common.variables import Variables as var

class Variables:
    symbol = ""
    timeframe = ""
    connection = ""	
    wallet = ""
    env = ""
    program_id = ""
    opts = None
    authority = None
    account_subscription = None
    perp_market_indexes = []
    spot_market_indexes = []
    oracle_infos = {}
    tx_params = None
    tx_version = None
    tx_sender = None
    active_sub_account_id = 0
    sub_account_ids = []
    market_lookup_table = None
    name: str
    qwe = 0
    testnet = True
    api_key = ""
    api_secret = ""
    ws_url = ""
    http_url = ""
    symbol_list = list()
    category_list = list()
    positions = OrderedDict()
    logger = logging
    logNumFatal = ""
    connect_count = 0
    user_id = None
    user = dict()
    message_time = datetime.now(tz=timezone.utc)
    message2000 = ""
    messageStopped = ""
    maxRetryRest = 3
    symbol_category = ""
    currency_divisor = dict()
    filename = ""
    api_is_active = False
    session: requests.Session