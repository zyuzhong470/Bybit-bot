from indicators import ma, atr, ma_slope
import config

def get_signal(data, current_price):
    if data is None or len(data) < config.MA_PERIOD:
        return "HOLD"

    ma120 = ma(data, config.MA_PERIOD)
    slope = ma_slope(data, config.MA_PERIOD)   # 需要实现斜率函数
    atr_val = atr(data, config.ATR_PERIOD)
    atr_pct = atr_val / current_price

    # 波动过滤
    if atr_pct < config.MIN_ATR_PCT or atr_pct > config.MAX_ATR_PCT:
        return "HOLD"

    # 趋势过滤（斜率方向）
    price = current_price
    if price > ma120 and slope > config.MA_SLOPE_THRESHOLD:
        return "LONG"
    elif price < ma120 and slope < -config.MA_SLOPE_THRESHOLD:
        return "SHORT"
    else:
        return "HOLD"
