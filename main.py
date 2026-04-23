import threading, time, traceback
from config import SYMBOL, INTERVAL, RISK_PER_TRADE, ATR_STOP_MULT, MAX_POSITION_VALUE_RATIO, MAX_PRICE_DIFF_PCT
from bybit_client import BybitClient
from websocket_feed import PriceFeed
from strategy import get_signal
from indicators import atr
from risk import check_risk_allowed, update_equity_and_drawdown
from execution import sync_position, open_position, close_position
from health import record_error, reset_health, is_system_healthy
from logger import log
from utils import sleep_until_next_interval
import state_machine as sm

client = BybitClient()
feed = PriceFeed(SYMBOL, INTERVAL)

def calc_position_size(balance, price, atr_value):
    risk_amount = balance * RISK_PER_TRADE
    stop_dist = atr_value * ATR_STOP_MULT
    if stop_dist <= 0:
        return 0
    pos_value = risk_amount * price / stop_dist
    max_value = balance * MAX_POSITION_VALUE_RATIO
    if pos_value > max_value:
        pos_value = max_value
    qty = pos_value / price
    return round(qty, 3)

def get_klines_rest():
    return client.get_klines(INTERVAL, limit=200)

def main():
    log("🚀 SOP v2.8 抗震荡版启动")
    feed.start()
    time.sleep(2)

    klines_cache = None
    last_rest = 0

    while True:
        try:
            # 1. 刷新K线缓存
            if time.time() - last_rest > 60:
                klines_cache = get_klines_rest()
                last_rest = time.time()
                if klines_cache is None:
                    time.sleep(10)
                    continue

            # 2. 获取价格（双通道一致性校验）
            ws_kline = feed.get_latest_kline()
            rest_kline = klines_cache[-1] if klines_cache else None
            if ws_kline and rest_kline:
                ws_price = float(ws_kline[4])
                rest_price = float(rest_kline[4])
                price_diff = abs(ws_price - rest_price) / rest_price
                if price_diff > MAX_PRICE_DIFF_PCT:
                    log(f"WS/REST 价格差异 {price_diff:.4%}，跳过交易")
                    time.sleep(10)
                    continue
                current_price = ws_price
            elif ws_kline:
                current_price = float(ws_kline[4])
            elif rest_kline:
                current_price = float(rest_kline[4])
            else:
                time.sleep(1)
                continue

            # 3. 风控检查
            if not check_risk_allowed():
                time.sleep(60)
                continue

            # 4. 同步持仓
            position = sync_position()
            in_position = position is not None

            # 5. 状态机
            cur_state = sm.get_state()
            if in_position and cur_state != "IN_POSITION":
                sm.transition("IN_POSITION")
            elif not in_position and cur_state == "IN_POSITION":
                sm.transition("IDLE")

            # 6. 计算 ATR 和信号
            atr_val = atr(klines_cache, 14) if klines_cache else 0.5
            signal = get_signal(klines_cache, current_price)
            log(f"状态:{cur_state} 信号:{signal} 价格:{current_price} ATR:{atr_val:.4f}")

            # 7. 交易执行（状态机限制）
            if cur_state == "IDLE":
                if signal == "LONG":
                    bal = client.get_wallet_balance()
                    qty = calc_position_size(bal, current_price, atr_val)
                    if qty > 0 and open_position("Buy", qty, current_price, atr_val):
                        sm.transition("IN_POSITION")
                elif signal == "SHORT":
                    bal = client.get_wallet_balance()
                    qty = calc_position_size(bal, current_price, atr_val)
                    if qty > 0 and open_position("Sell", qty, current_price, atr_val):
                        sm.transition("IN_POSITION")
            elif cur_state == "IN_POSITION":
                # 反手处理
                if signal == "LONG" and position and position["side"] == "Sell":
                    close_position(current_price)
                    sm.transition("IDLE")
                    bal = client.get_wallet_balance()
                    qty = calc_position_size(bal, current_price, atr_val)
                    if qty > 0 and open_position("Buy", qty, current_price, atr_val):
                        sm.transition("IN_POSITION")
                elif signal == "SHORT" and position and position["side"] == "Buy":
                    close_position(current_price)
                    sm.transition("IDLE")
                    bal = client.get_wallet_balance()
                    qty = calc_position_size(bal, current_price, atr_val)
                    if qty > 0 and open_position("Sell", qty, current_price, atr_val):
                        sm.transition("IN_POSITION")

            # 8. 输出状态
            equity = update_equity_and_drawdown()
            log(f"权益:{equity:.2f} 日PnL:{load_state()['daily_pnl']:.2f}")

            sleep_until_next_interval(INTERVAL)

        except Exception as e:
            log(f"主循环异常: {traceback.format_exc()}", "ERROR")
            record_error()
            time.sleep(10)
            if not is_system_healthy():
                log("系统不健康，暂停5分钟", "WARNING")
                time.sleep(300)
                reset_health()

if __name__ == "__main__":
    main()
