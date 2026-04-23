import json, os, threading, time

STATE_FILE = "data/state.json"
_lock = threading.Lock()

def _ensure_dir():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

def _default_state():
    return {
        "in_position": False,
        "side": None,
        "entry_price": 0.0,
        "qty": 0.0,
        "order_link_id": None,
        "daily_pnl": 0.0,
        "consecutive_losses": 0,
        "cooldown_until": 0.0,
        "last_day": None,
        "peak_equity": 0.0,
        "max_drawdown": 0.0,
        "seen_exec_ids": [],           # 滑动窗口去重
        "last_trade_time": 0,          # 上次开仓时间
        "last_sync_time": 0,
    }

def load_state():
    with _lock:
        _ensure_dir()
        if not os.path.exists(STATE_FILE):
            return _default_state()
        with open(STATE_FILE, "r") as f:
            return json.load(f)

def save_state(state):
    with _lock:
        _ensure_dir()
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

def atomic_update(updater):
    with _lock:
        s = load_state()
        new_s = updater(s)
        save_state(new_s)
        return new_s

def reset_daily_if_new_day():
    def _reset(s):
        today = time.strftime("%Y-%m-%d")
        if s.get("last_day") != today:
            s["daily_pnl"] = 0.0
            s["last_day"] = today
        return s
    return atomic_update(_reset)
