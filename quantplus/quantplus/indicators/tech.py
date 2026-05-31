import pandas as pd
import numpy as np

class IndicatorCalculator:
    def __init__(self, prefer: str = "talib"):
        self.prefer = prefer.lower()

    def sma(self, series: pd.Series, period: int = 20) -> pd.Series:
        return series.rolling(window=period).mean()

    def ema(self, series: pd.Series, period: int = 20) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    def rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        try:
            if self.prefer == "talib":
                import talib
                return pd.Series(talib.RSI(close.values, timeperiod=period), index=close.index)
        except ImportError:
            pass
        # 回退到 stockstats 或手写
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def macd(self, close: pd.Series, fast=12, slow=26, signal=9):
        ema_fast = self.ema(close, fast)
        ema_slow = self.ema(close, slow)
        dif = ema_fast - ema_slow
        dea = self.ema(dif, signal)
        hist = 2 * (dif - dea)
        return pd.DataFrame({"DIF": dif, "DEA": dea, "MACD": hist})

    def bollinger_bands(self, close: pd.Series, period=20, nbdev=2):
        sma = self.sma(close, period)
        std = close.rolling(period).std()
        upper = sma + nbdev * std
        lower = sma - nbdev * std
        return pd.DataFrame({"MID": sma, "UPPER": upper, "LOWER": lower})