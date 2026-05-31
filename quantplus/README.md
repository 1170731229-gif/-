# QuantPlus

量化交易框架

## 安装

```bash
pip install -e .
```

## 快速开始

```python
import pandas as pd
from quantplus.data.fetcher import get_fetcher
from quantplus.indicators import tech
from quantplus.analysis.metrics import calculate_metrics
from quantplus.backtest.engine import backtest

# 获取数据
fetcher = get_fetcher()
data = fetcher.fetch_bars("AAPL", start_date, end_date)

# 计算指标
data["sma"] = tech.SMA(data["close"], 20)
data["rsi"] = tech.RSI(data["close"])

# 定义策略
def simple_strategy(data, state):
    if len(data) < 20:
        return {"action": None}
    if data["close"].iloc[-1] > data["sma"].iloc[-1]:
        return {"action": "buy", "quantity": 100}
    elif data["close"].iloc[-1] < data["sma"].iloc[-1]:
        return {"action": "sell", "quantity": 100}
    return {"action": None}

# 运行回测
result = backtest(data, simple_strategy)
print(calculate_metrics(result["equity_curve"]))
```

## 模块

- `data` - 数据获取
- `indicators` - 技术指标
- `analysis` - 绩效分析
- `visualization` - 可视化
- `backtest` - 回测引擎