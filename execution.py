import time, uuid, threading
from bybit_client import BybitClient
from state import atomic_update, load_state
from risk import mark_trade_result
from logger import log
import config

client = BybitClient()
_trade_lock = threading.Lock()

def generate_order_link_id():
    return f"{config.ORDER_ID_PREFIX}{uuid.uuid4().hex}"

def has_open_orders():
    for o in client.get_open_orders():
        if o.get("orderLinkId", "").startswith(config.ORDER_ID_PREFIX):
            return True
    return False

def sync_position(force=False):
    pos = client.get_position()
    if pos is None or float(pos["size"]) == 0:
        atomic_update(lambda s: {**s, "in_position": False, "side": None, "entry_price": 0.0, "qty": 0.0, "order_link_id": None})
        return None
    else:
        side = "Buy" if float(pos["size"]) > 0 else "Sell"
        qty = abs(float(pos["size"]))
        entry = float(pos["avgPrice"])
        atomic_update(lambda s: {**s, "in_position": True, "side": side, "entry_price": entry, "qty": qty})
        return {"side": side, "qty": qty, "entry_price": entry}

def _verify_sl_tp(side, expected_sl, expected_tp, retries=3):
    for _ in range(retries):
        pos = client.get_position()
        if pos:
            actual_sl = float(pos.get("stopLoss", 0))
            actual_tp = float(pos.get("takeProfit", 0))
            if abs(actual_sl - expected_sl) < 0.01 and abs(actual_tp - expected_tp) < 0.01:
                return True
        client.set_trading_stop(side, stop_loss=expected_sl, take_profit=expected_tp)
        time.sleep(1)
    return False

def open_position(side, qty, signal_price, atr_value):
    with _trade_lock:
        if has_open_orders():
            log("已有挂单，禁止开仓")
            return False
        sync_position()
        if load_state()["in_position"]:
            log("已有持仓")
            return False

        if side == "Buy":
            sl = signal_price - atr_value * config.ATR_STOP_MULT
            tp = signal_price + atr_value * config.ATR_TAKE_MULT
        else:
            sl = signal_price + atr_value * config.ATR_STOP_MULT
            tp = signal_price - atr_value * config.ATR_TAKE_MULT

        oid = generate_order_link_id()
        resp = client.place_order(side, qty, oid)
        if resp["retCode"] != 0:
            log(f"开仓失败: {resp}")
            return False

        # 确认成交
        for _ in range(10):
            time.sleep(1)
            pos = sync_position()
            if pos and pos["side"] == side:
                entry_price = pos["entry_price"]
                # 滑点检查
                slippage = abs(entry_price - signal_price) / signal_price
                if slippage > config.MAX_SLIPPAGE_PCT:
                    log(f"滑点过大 {slippage:.4%}，立即平仓")
                    close_position(entry_price)
                    return False
                # 挂止盈止损
                client.set_trading_stop(side, stop_loss=sl, take_profit=tp)
                if _verify_sl_tp(side, sl, tp):
                    atomic_update(lambda s: {**s, "order_link_id": oid})
                    log(f"开仓成功 {side} {qty} @ {entry_price:.4f} (信号价 {signal_price:.4f}) SL={sl:.4f} TP={tp:.4f}")
                    return True
                else:
                    log("止损挂载失败，平仓避险")
                    close_position(entry_price)
                    return False
        log("开仓超时未确认")
        return False

def close_position(current_price):
    with _trade_lock:
        state = load_state()
        if not state["in_position"]:
            return False
        side = state["side"]
        qty = state["qty"]
        entry = state["entry_price"]
        close_side = "Sell" if side == "Buy" else "Buy"
        oid = generate_order_link_id()
        resp = client.place_order(close_side, qty, oid, reduce_only=True)
        if resp["retCode"] != 0:
            log(f"平仓失败: {resp}")
            return False
        for _ in range(10):
            time.sleep(1)
            if sync_position() is None:
                if side == "Buy":
                    pnl = (current_price - entry) * qty
                else:
                    pnl = (entry - current_price) * qty
                fee = (entry * qty + current_price * qty) * 0.0006
                pnl -= fee
                mark_trade_result(pnl)
                log(f"平仓完成 PnL={pnl:.2f}")
                return True
        log("平仓超时未确认")
        return False
