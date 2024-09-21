import logging
from collections import OrderedDict
from datetime import datetime, timezone

import requests

from common.variables import Variables as var


class Variables:
    connection = ""	
    wallet = ""
    env = ""
    program_id = ""
    opts
    authority
    account_subscription
    perp_market_indexes
    spot_market_indexes	
    oracle_infos
    tx_params	
    tx_version	
    tx_sender
    active_sub_account_id
    sub_account_ids	
    market_lookup_table


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