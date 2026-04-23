import time
from state import atomic_update, load_state, reset_daily_if_new_day
from pnl import sync_realized_pnl
from bybit_client import BybitClient
from health import is_system_healthy
import config

client = BybitClient()

def update_equity_and_drawdown():
    equity = client.get_wallet_balance()
    def _update(s):
        if equity > s["peak_equity"]:
            s["peak_equity"] = equity
        if s["peak_equity"] > 0:
            dd = (s["peak_equity"] - equity) / s["peak_equity"]
            if dd > s["max_drawdown"]:
                s["max_drawdown"] = dd
        return s
    atomic_update(_update)
    return equity

def check_risk_allowed():
    # 1. 系统健康
    if not is_system_healthy():
        print("⚠️ 系统错误过多，暂停")
        return False
    # 2. 同步已实现 PnL
    reset_daily_if_new_day()
    sync_realized_pnl()
    # 3. 更新回撤
    equity = update_equity_and_drawdown()
    state = load_state()
    # 4. 最大回撤熔断
    if state["max_drawdown"] >= config.MAX_DRAWDOWN:
        print(f"⚠️ 回撤 {state['max_drawdown']:.2%} 熔断")
        return False
    # 5. 日亏损（修正：用比例比较）
    max_loss_abs = equity * config.MAX_DAILY_LOSS
    if state["daily_pnl"] <= -max_loss_abs:
        print(f"⚠️ 日亏损 {state['daily_pnl']:.2f} (限 {max_loss_abs:.2f}) 熔断")
        return False
    # 6. 连败冷却
    if state["consecutive_losses"] >= config.MAX_CONSECUTIVE_LOSSES:
        if time.time() < state.get("cooldown_until", 0):
            print(f"⚠️ 连败冷却中")
            return False
        else:
            atomic_update(lambda s: {**s, "consecutive_losses": 0})
    # 7. 交易频率限制
    last_trade = state.get("last_trade_time", 0)
    if time.time() - last_trade < config.MIN_TRADE_INTERVAL:
        print(f"⚠️ 交易频率限制，距上次开仓 {int((time.time()-last_trade)/60)} 分钟")
        return False
    return True

def mark_trade_result(pnl):
    def _update(s):
        s["consecutive_losses"] = (s["consecutive_losses"] + 1) if pnl < 0 else 0
        s["last_trade_time"] = time.time()
        return s
    atomic_update(_update)
    new = load_state()
    if new["consecutive_losses"] >= config.MAX_CONSECUTIVE_LOSSES:
        atomic_update(lambda s: {**s, "cooldown_until": time.time() + config.COOLDOWN_MINUTES * 60})
