import time
from bybit_client import BybitClient
from state import atomic_update, load_state

client = BybitClient()

def sync_realized_pnl():
    state = load_state()
    seen_ids = set(state.get("seen_exec_ids", []))
    last_ts = state.get("last_pnl_sync_time", 0)
    now_ms = int(time.time() * 1000)

    executions = client.get_executions(start_time_ms=last_ts if last_ts else None, limit=200)
    if not executions:
        return 0.0

    new_execs = []
    total_pnl = 0.0
    for ex in executions:
        exec_id = ex["execId"]
        if exec_id not in seen_ids:
            new_execs.append(ex)
            seen_ids.add(exec_id)
            total_pnl += float(ex.get("execPnl", 0))

    if total_pnl != 0:
        # 保留最近 200 个 ID，防止内存膨胀
        limited_seen = list(seen_ids)[-200:]
        def update(s):
            s["daily_pnl"] += total_pnl
            s["last_pnl_sync_time"] = now_ms
            s["seen_exec_ids"] = limited_seen
            return s
        atomic_update(update)
    return total_pnl
