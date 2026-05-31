"""
QuantPlus - 量化交易框架
"""

__version__ = "0.1.0"

from . import data
from . import indicators
from . import analysis
from . import visualization
from . import backtest
from . import factor
from . import ml

from .data.fetcher import AkshareSource, TushareSource, BaostockSource, create_data_source
from .indicators.tech import IndicatorCalculator
from .analysis.metrics import sharpe_ratio, max_drawdown, calculate_metrics
from .backtest.engine import run_backtest, StrategyTemplate
from .backtest.t0_strategies import DailyT0Strategy, GridT0Strategy, VolatilityT0Strategy
from .backtest.advanced_t0 import EnhancedT0Strategy, GridT0StrategyAdvanced, TrendT0Strategy
from .visualization.charts import plot_candlestick
from datetime import datetime, timedelta


class QuantPlus:
    def __init__(self, data_source="akshare", token=None):
        if data_source == "tushare":
            self.source = TushareSource(token)
        elif data_source == "baostock":
            self.source = BaostockSource()
        else:
            self.source = AkshareSource()
        self.calc = IndicatorCalculator()
        self.data = None

    def fetch(self, symbol, start=None, end=None):
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")
        if start is None:
            start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        self.data = self.source.get_daily(symbol, start, end)
        return self.data

    def fetch_minute(self, symbol, period="5", days=5):
        """获取分钟级数据
        period: '5', '15', '30', '60' 分钟
        days: 获取最近多少天的数据
        """
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        self.data = self.source.get_minute(symbol, start, end, period)
        return self.data

    def add_indicators(self, config: dict):
        if self.data is None:
            raise ValueError("请先调用 fetch 获取数据")
        for name, params in config.items():
            if name == "sma":
                self.data["SMA"] = self.calc.sma(self.data["close"], params)
            elif name == "rsi":
                self.data["RSI"] = self.calc.rsi(self.data["close"], params)
            elif name == "macd":
                macd_df = self.calc.macd(self.data["close"])
                self.data["DIF"] = macd_df["DIF"]
                self.data["DEA"] = macd_df["DEA"]
                self.data["MACD"] = macd_df["MACD"]
        return self.data

    def view(self, indicators=None):
        if indicators is None:
            indicators = ["SMA"]
        indicator_dict = {ind: self.data[ind] for ind in indicators if ind in self.data.columns}
        fig = plot_candlestick(self.data, indicator_dict)
        fig.show()

    def backtest(self, strategy_class, cash=100000, comm=0.001):
        return run_backtest(strategy_class, self.data, initial_cash=cash, commission=comm)


__all__ = [
    "QuantPlus",
    "AkshareSource",
    "TushareSource",
    "BaostockSource",
    "create_data_source",
    "IndicatorCalculator",
    "sharpe_ratio",
    "max_drawdown",
    "calculate_metrics",
    "run_backtest",
    "StrategyTemplate",
    "DailyT0Strategy",
    "GridT0Strategy",
    "VolatilityT0Strategy",
    "EnhancedT0Strategy",
    "GridT0StrategyAdvanced",
    "TrendT0Strategy",
    "plot_candlestick",
]