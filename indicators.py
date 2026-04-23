import numpy as np

def ma(data, period=120):
    closes = [float(i[4]) for i in data]
    if len(closes) < period:
        return closes[-1]
    return np.mean(closes[-period:])

def atr(data, period=14):
    highs = [float(i[2]) for i in data]
    lows = [float(i[3]) for i in data]
    closes = [float(i[4]) for i in data]
    trs = []
    for i in range(1, len(data)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        return np.mean(trs) if trs else 0
    return np.mean(trs[-period:])

def ma_slope(data, period=120):
    """计算 MA 的线性回归斜率（点数/周期）"""
    closes = [float(i[4]) for i in data]
    if len(closes) < period:
        return 0
    ma_vals = [np.mean(closes[i-period:i]) for i in range(period, len(closes))]
    if len(ma_vals) < 2:
        return 0
    x = np.arange(len(ma_vals))
    slope = np.polyfit(x, ma_vals, 1)[0]
    # 归一化到价格比例
    return slope / ma_vals[-1] if ma_vals[-1] != 0 else 0
