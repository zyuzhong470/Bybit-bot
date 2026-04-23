import time
from pybit.unified_trading import HTTP
import config

class BybitClient:
    def __init__(self):
        self.session = HTTP(
            testnet=config.TESTNET,
            api_key=config.API_KEY,
            api_secret=config.API_SECRET,
        )
        self._set_leverage()

    def _set_leverage(self):
        try:
            self.session.set_leverage(
                category="linear",
                symbol=config.SYMBOL,
                buyLeverage=str(config.LEVERAGE),
                sellLeverage=str(config.LEVERAGE),
            )
        except Exception as e:
            print(f"杠杆设置失败: {e}")

    def _retry(func):
        def wrapper(self, *args, **kwargs):
            for i in range(config.MAX_API_RETRIES):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    print(f"API 调用失败 ({i+1}/{config.MAX_API_RETRIES}): {e}")
                    time.sleep(config.API_RETRY_DELAY)
            return None
        return wrapper

    @_retry
    def get_wallet_balance(self):
        resp = self.session.get_wallet_balance(accountType="UNIFIED")
        if resp["retCode"] == 0:
            return float(resp["result"]["list"][0]["totalEquity"])
        return 0.0

    @_retry
    def get_position(self):
        resp = self.session.get_positions(category="linear", symbol=config.SYMBOL)
        if resp["retCode"] == 0 and resp["result"]["list"]:
            return resp["result"]["list"][0]
        return None

    @_retry
    def place_order(self, side, qty, order_link_id, order_type="Market", reduce_only=False):
        return self.session.place_order(
            category="linear",
            symbol=config.SYMBOL,
            side=side,
            orderType=order_type,
            qty=str(qty),
            timeInForce="GoodTillCancel",
            reduceOnly=reduce_only,
            orderLinkId=order_link_id,
        )

    @_retry
    def set_trading_stop(self, side, stop_loss=None, take_profit=None):
        params = {"category": "linear", "symbol": config.SYMBOL, "side": side}
        if stop_loss:
            params["stopLoss"] = str(stop_loss)
            params["slTriggerBy"] = "LastPrice"
        if take_profit:
            params["takeProfit"] = str(take_profit)
            params["tpTriggerBy"] = "LastPrice"
        return self.session.set_trading_stop(**params)

    @_retry
    def get_executions(self, start_time_ms=None, limit=200):
        params = {"category": "linear", "symbol": config.SYMBOL, "limit": limit}
        if start_time_ms:
            params["startTime"] = start_time_ms
        resp = self.session.get_executions(**params)
        if resp["retCode"] != 0:
            return []
        return resp["result"]["list"]

    @_retry
    def get_open_orders(self):
        resp = self.session.get_open_orders(category="linear", symbol=config.SYMBOL)
        return resp["result"]["list"] if resp["retCode"] == 0 else []

    @_retry
    def get_klines(self, interval, limit=200):
        resp = self.session.get_kline(
            category="linear",
            symbol=config.SYMBOL,
            interval=interval,
            limit=limit,
        )
        return resp["result"]["list"] if resp["retCode"] == 0 else None

    @_retry
    def cancel_all_orders(self):
        return self.session.cancel_all_orders(category="linear", symbol=config.SYMBOL)
