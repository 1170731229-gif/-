"""
因子评估模块 - IC分析、因子有效性检验
"""

import pandas as pd
import numpy as np
from typing import List, Optional


class FactorEvaluator:
    @staticmethod
    def calculate_ic(
        factor_df: pd.DataFrame,
        factor_col: str,
        label_col: str = "label",
        method: str = "spearman",
        date_col: str = "date"
    ) -> pd.Series:
        """计算因子IC值（信息系数）"""
        if date_col in factor_df.columns:
            factor_df = factor_df.copy()
            factor_df["_period"] = pd.to_datetime(factor_df[date_col]).dt.to_period("M")
            grouped = factor_df.groupby("_period")
        else:
            grouped = factor_df.groupby(factor_df.index.to_period("M"))
        
        ic_series = grouped.apply(
            lambda x: x[factor_col].corr(x[label_col], method=method)
        )
        ic_series.name = factor_col
        return ic_series
    
    @staticmethod
    def calculate_ir(
        ic_series: pd.Series,
        rolling_window: int = 12
    ) -> float:
        """计算因子IR（信息比率）"""
        ic_mean = ic_series.mean()
        ic_std = ic_series.rolling(window=rolling_window).std().iloc[-1]
        if ic_std == 0:
            return 0.0
        return ic_mean / ic_std
    
    @staticmethod
    def factor_quantile_analysis(
        factor_df: pd.DataFrame,
        factor_col: str,
        label_col: str = "label",
        quantiles: int = 5
    ) -> pd.DataFrame:
        """因子分位数分析"""
        factor_df = factor_df.copy()
        factor_df["quantile"] = pd.qcut(
            factor_df[factor_col], q=quantiles, labels=False, duplicates="drop"
        )
        
        result = factor_df.groupby("quantile").agg({
            factor_col: ["mean", "std"],
            label_col: ["mean", "std", "sum"]
        })
        return result
    
    @staticmethod
    def calculate_cumulative_return(
        factor_df: pd.DataFrame,
        factor_col: str,
        label_col: str = "label",
        quantiles: int = 5,
        periods: int = 5
    ) -> pd.DataFrame:
        """计算因子各分位数组合的累计收益"""
        factor_df = factor_df.copy()
        factor_df["quantile"] = pd.qcut(
            factor_df[factor_col], q=quantiles, labels=False, duplicates="drop"
        )
        # 使用向量化计算前向收益，避免对每个分位做重复的 pct_change
        factor_df["forward_return"] = factor_df.groupby("quantile")["close"].pct_change(periods).shift(-periods)

        # 为保持与原实现兼容，按分位收集并对齐为 DataFrame
        returns_by_quantile = {
            f"Q{q+1}": factor_df.loc[factor_df["quantile"] == q, "forward_return"].dropna().reset_index(drop=True)
            for q in range(quantiles)
        }

        return pd.DataFrame(returns_by_quantile).cumsum()
    
    @staticmethod
    def neutralization_report(
        factor_df: pd.DataFrame,
        factor_col: str,
        neutralize_cols: List[str] = None
    ) -> dict:
        """因子中性化报告"""
        if neutralize_cols is None:
            neutralize_cols = ["market_cap", "volume_ma_ratio_20"]
        
        report = {
            "raw_ic": factor_df[factor_col].corr(factor_df["label"], method="spearman"),
            "neutralized_ic": None,
        }
        
        available_cols = [c for c in neutralize_cols if c in factor_df.columns]
        if available_cols:
            from sklearn.linear_model import LinearRegression
            
            X = factor_df[available_cols].values
            y = factor_df[factor_col].values
            
            model = LinearRegression()
            model.fit(X, y)
            residuals = y - model.predict(X)
            
            factor_df = factor_df.copy()
            factor_df["neutralized_factor"] = residuals
            
            report["neutralized_ic"] = (
                factor_df["neutralized_factor"].corr(factor_df["label"], method="spearman")
            )
        
        return report
    
    @staticmethod
    def full_evaluation(
        factor_df: pd.DataFrame,
        factor_col: str,
        label_col: str = "label"
    ) -> dict:
        """完整因子评估报告"""
        ic_series = FactorEvaluator.calculate_ic(factor_df, factor_col, label_col)
        
        return {
            "ic_mean": ic_series.mean(),
            "ic_std": ic_series.std(),
            "ic_ir": ic_series.mean() / ic_series.std() if ic_series.std() != 0 else 0,
            "ic_positive_rate": (ic_series > 0).mean(),
            "quantile_analysis": FactorEvaluator.factor_quantile_analysis(
                factor_df, factor_col, label_col
            )
        }