"""
通用工具函数
"""

from datetime import datetime
import pandas as pd


def parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    formats = ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def format_number(num: float, decimals: int = 2) -> str:
    """格式化数字"""
    return f"{num:.{decimals}f}"


def resample_bars(data: pd.DataFrame, freq: str) -> pd.DataFrame:
    """重新采样K线"""
    df = data.set_index("datetime")
    resampled = df.resample(freq).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    })
    return resampled.dropna()