import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY", "")
API_SECRET = os.getenv("BYBIT_API_SECRET", "")
SYMBOL = os.getenv("SYMBOL", "SOLUSDT")
TESTNET = os.getenv("TESTNET", "True").lower() == "true"

# 策略参数
INTERVAL = 15
MA_PERIOD = 120
ATR_PERIOD = 14
ATR_STOP_MULT = 2.0
ATR_TAKE_MULT = 4.0          # 盈亏比 4:1

# 风控参数
MAX_DAILY_LOSS = 0.12         # 12% 已实现亏损
MAX_CONSECUTIVE_LOSSES = 3
COOLDOWN_MINUTES = 120
MAX_DRAWDOWN = 0.15           # 15% 回撤
MAX_SYSTEM_ERRORS = 5
ERROR_WINDOW_SEC = 300

# 仓位管理
RISK_PER_TRADE = 0.02
LEVERAGE = 3
MAX_POSITION_VALUE_RATIO = 0.2

# 订单幂等前缀
ORDER_ID_PREFIX = "sop_"

# API 重试
MAX_API_RETRIES = 3
API_RETRY_DELAY = 1

# WebSocket
WS_RECONNECT_DELAY = 5

# 交易频率限制（秒）
MIN_TRADE_INTERVAL = 1800     # 30分钟

# 滑点容忍度（百分比）
MAX_SLIPPAGE_PCT = 0.003      # 0.3%

# WS/REST 价格差异容忍度（百分比）
MAX_PRICE_DIFF_PCT = 0.002    # 0.2%

# 波动过滤
MIN_ATR_PCT = 0.005           # ATR 低于价格的 0.5% 不交易
MAX_ATR_PCT = 0.05            # ATR 高于价格的 5% 不交易

# 趋势过滤（MA120 斜率）
MA_SLOPE_THRESHOLD = 0.0001   # 最小斜率绝对值

# 日志
LOG_LEVEL = "INFO"
