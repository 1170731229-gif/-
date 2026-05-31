"""
特征工程模块 - 避免未来信息泄露的特征构建器
"""

import pandas as pd
import numpy as np
from typing import List, Callable, Optional


class FactorBuilder:
    def __init__(self):
        self.factors = {}
    
    def add_return_factor(
        self,
        periods: List[int] = None,
        prefix: str = ""
    ) -> "FactorBuilder":
        if periods is None:
            periods = [1, 5, 10, 20]
        for p in periods:
            col_name = f"{prefix}return_{p}" if prefix else f"return_{p}"
            self.factors[col_name] = lambda df, period=p: (
                df["close"].pct_change(period)
            )
        return self
    
    def add_ma_factor(
        self,
        periods: List[int] = None,
        prefix: str = ""
    ) -> "FactorBuilder":
        if periods is None:
            periods = [5, 10, 20, 60]
        for p in periods:
            col_name = f"{prefix}ma_{p}" if prefix else f"ma_{p}"
            self.factors[col_name] = lambda df, period=p: (
                df["close"].rolling(window=period).mean()
            )
        return self
    
    def add_ma_ratio_factor(
        self,
        periods: List[int] = None,
        prefix: str = ""
    ) -> "FactorBuilder":
        if periods is None:
            periods = [(5, 20), (10, 60), (20, 120)]
        for short, long in periods:
            col_name = f"{prefix}ma_ratio_{short}_{long}" if prefix else f"ma_ratio_{short}_{long}"
            self.factors[col_name] = lambda df, s=short, l=long: (
                df["close"].rolling(s).mean() / df["close"].rolling(l).mean()
            )
        return self
    
    def add_volatility_factor(
        self,
        periods: List[int] = None,
        prefix: str = ""
    ) -> "FactorBuilder":
        if periods is None:
            periods = [5, 10, 20]
        for p in periods:
            col_name = f"{prefix}volatility_{p}" if prefix else f"volatility_{p}"
            self.factors[col_name] = lambda df, period=p: (
                df["close"].pct_change().rolling(window=period).std()
            )
        return self
    
    def add_volume_factor(
        self,
        periods: List[int] = None,
        prefix: str = ""
    ) -> "FactorBuilder":
        if periods is None:
            periods = [5, 20]
        for p in periods:
            col_name = f"{prefix}volume_ma_ratio_{p}" if prefix else f"volume_ma_ratio_{p}"
            self.factors[col_name] = lambda df, period=p: (
                df["volume"] / df["volume"].rolling(window=period).mean()
            )
        return self
    
    def add_rsi_factor(
        self,
        periods: List[int] = None,
        prefix: str = ""
    ) -> "FactorBuilder":
        if periods is None:
            periods = [6, 12, 24]
        for p in periods:
            col_name = f"{prefix}rsi_{p}" if prefix else f"rsi_{p}"
            self.factors[col_name] = lambda df, period=p: self._calculate_rsi(df["close"], period)
        return self
    
    def add_momentum_factor(
        self,
        periods: List[int] = None,
        prefix: str = ""
    ) -> "FactorBuilder":
        if periods is None:
            periods = [5, 10, 20]
        for p in periods:
            col_name = f"{prefix}momentum_{p}" if prefix else f"momentum_{p}"
            self.factors[col_name] = lambda df, period=p: (
                df["close"] / df["close"].shift(period) - 1
            )
        return self
    
    def add_custom_factor(
        self,
        name: str,
        func: Callable[[pd.DataFrame], pd.Series]
    ) -> "FactorBuilder":
        self.factors[name] = func
        return self
    
    @staticmethod
    def _calculate_rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))
    
    def build(
        self,
        df: pd.DataFrame,
        forward: int = 1,
        label_type: str = "binary",
        threshold: float = 0.0
    ) -> pd.DataFrame:
        result = df.copy()
        
        for name, func in self.factors.items():
            result[name] = func(df)
        
        if forward > 0:
            if label_type == "binary":
                result["label"] = (
                    result["close"].shift(-forward) / result["close"] - 1
                ) > threshold
                result["label"] = result["label"].astype(int)
            elif label_type == "regression":
                result["label"] = (
                    result["close"].shift(-forward) / result["close"] - 1
                )
            elif label_type == "direction":
                result["label"] = (
                    result["close"].shift(-forward) > result["close"]
                ).astype(int)
        
        return result.dropna()


def create_default_builder() -> FactorBuilder:
    """创建默认特征构建器"""
    return (
        FactorBuilder()
        .add_return_factor()
        .add_ma_factor()
        .add_ma_ratio_factor()
        .add_volatility_factor()
        .add_volume_factor()
        .add_rsi_factor()
        .add_momentum_factor()
    )