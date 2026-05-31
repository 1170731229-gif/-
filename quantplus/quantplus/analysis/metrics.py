import numpy as np
import pandas as pd
from typing import Dict


def annual_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Annualized return from a series of periodic returns."""
    returns = returns.dropna()
    if returns.empty:
        return np.nan
    gross = (1 + returns).prod()
    return gross ** (periods_per_year / len(returns)) - 1


def annual_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Annualized volatility (sample std, ddof=1)."""
    returns = returns.dropna()
    if returns.empty:
        return np.nan
    return returns.std(ddof=1) * np.sqrt(periods_per_year)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    """Annualized Sharpe ratio using sample std (ddof=1).

    `risk_free_rate` is expected as an annual rate (e.g. 0.02 for 2%).
    """
    returns = returns.dropna()
    if returns.empty:
        return np.nan
    rf_per_period = risk_free_rate / periods_per_year
    excess = returns - rf_per_period
    std = excess.std(ddof=1)
    if std == 0 or np.isnan(std):
        return np.nan
    return np.sqrt(periods_per_year) * excess.mean() / std


def max_drawdown(equity_curve: pd.Series) -> float:
    """Maximum drawdown from an equity curve (series of portfolio values).

    Returns a negative number (the worst drawdown, e.g. -0.35 for -35%).
    """
    eq = equity_curve.dropna().astype(float)
    if eq.empty:
        return 0.0
    cumulative = eq / eq.iloc[0]
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    return drawdown.min()


def calmar_ratio(equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    """Calmar ratio: annualized return divided by max drawdown (abs).

    If drawdown is zero returns `np.nan`.
    """
    returns = equity_curve.pct_change().dropna()
    ann_ret = annual_return(returns, periods_per_year) if len(returns) > 0 else np.nan
    dd = abs(max_drawdown(equity_curve))
    return ann_ret / dd if dd != 0 else np.nan


def calculate_metrics(equity_curve: pd.Series, periods_per_year: int = 252) -> Dict[str, float]:
    """Compute a concise set of performance metrics from an equity curve.

    Returns a dict with percentages for returns/drawdowns and raw ratios for others.
    """
    eq = equity_curve.dropna().astype(float)
    if eq.empty or len(eq) < 2:
        return {"error": "No equity data"}

    returns = eq.pct_change().dropna()

    total_return = (eq.iloc[-1] / eq.iloc[0] - 1) * 100
    annualized_return = annual_return(returns, periods_per_year) * 100
    max_dd = abs(max_drawdown(eq)) * 100
    sr = sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=periods_per_year)
    calmar = calmar_ratio(eq, periods_per_year)
    win_rate = (returns > 0).sum() / len(returns) * 100

    pos_mean = returns[returns > 0].mean() if (returns > 0).any() else 0.0
    neg_mean = returns[returns < 0].mean() if (returns < 0).any() else 0.0
    if np.isnan(pos_mean):
        pos_mean = 0.0
    if np.isnan(neg_mean):
        neg_mean = 0.0
    profit_loss_ratio = (pos_mean / abs(neg_mean)) if neg_mean != 0 else np.inf

    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "max_drawdown": max_dd,
        "sharpe_ratio": sr,
        "calmar_ratio": calmar,
        "win_rate": win_rate,
        "profit_loss_ratio": profit_loss_ratio,
    }