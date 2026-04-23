# SOP v2.8 抗震荡实盘版

## 修复内容
- execId 滑动窗口去重
- 日亏损单位修正（比例比较）
- 滑点保护（>0.3% 平仓）
- WS+REST 价格一致性校验
- 交易频率限制（30分钟最小间隔）
- 趋势过滤（MA斜率）
- 波动过滤（ATR 范围）
- 盈亏比优化（4:1）

## 部署
```bash
git clone https://github.com/你的用户名/sop-v2.8.git
cd sop-v2.8
cp .env.example .env
nano .env
bash install.sh
python3 main.py
