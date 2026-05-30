from abc import ABC, abstractmethod
import pandas as pd


class DataSource(ABC):
    @abstractmethod
    def get_daily(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """获取日线行情，返回列需包含: datetime, open, high, low, close, volume"""
        pass

    @abstractmethod
    def get_minute(self, symbol: str, start: str, end: str, period: str = "5") -> pd.DataFrame:
        """获取分钟级行情，返回列需包含: datetime, open, high, low, close, volume
        period: '5', '15', '30', '60' 分钟
        """
        pass


class AkshareSource(DataSource):
    def get_daily(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        import akshare as ak
        code = symbol.replace("sh", "").replace("sz", "")
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                start_date=start, end_date=end, adjust="qfq")
        df.rename(columns={
            "日期": "datetime", "开盘": "open", "最高": "high",
            "最低": "low", "收盘": "close", "成交量": "volume"
        }, inplace=True)
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df[["datetime", "open", "high", "low", "close", "volume"]]

    def get_minute(self, symbol: str, start: str, end: str, period: str = "5") -> pd.DataFrame:
        import akshare as ak
        code = symbol.replace("sh", "").replace("sz", "")
        period_map = {"5": "5", "15": "15", "30": "30", "60": "60", "120": "120"}
        period_code = period_map.get(period, "5")

        # 使用 minute 周期请求，而非 daily，避免获取不必要的大块日线数据
        df = ak.stock_zh_a_hist(symbol=code, period=period_code,
                                start_date=start, end_date=end, adjust="qfq")
        df.rename(columns={
            "日期": "datetime", "开盘": "open", "最高": "high",
            "最低": "low", "收盘": "close", "成交量": "volume"
        }, inplace=True)
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df[["datetime", "open", "high", "low", "close", "volume"]]


class TushareSource(DataSource):
    def __init__(self, token: str):
        import tushare as ts
        ts.set_token(token)
        self.pro = ts.pro_api()

    def get_daily(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        ts_code = self._format_symbol(symbol)
        df = self.pro.daily(ts_code=ts_code, start_date=start.replace("-", ""),
                            end_date=end.replace("-", ""))
        df.rename(columns={"trade_date": "datetime", "vol": "volume"}, inplace=True)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.sort_values("datetime", inplace=True)
        return df[["datetime", "open", "high", "low", "close", "volume"]]

    def get_minute(self, symbol: str, start: str, end: str, period: str = "5") -> pd.DataFrame:
        ts_code = self._format_symbol(symbol)
        period_map = {"5": "5min", "15": "15min", "30": "30min", "60": "60min"}
        period_code = period_map.get(period, "5min")

        df = self.pro.stk_mins(ts_code=ts_code, freq=period_code,
                               start_date=start.replace("-", "").replace(" ", ""),
                               end_date=end.replace("-", "").replace(" ", ""))
        df.rename(columns={"trade_time": "datetime", "vol": "volume"}, inplace=True)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.sort_values("datetime", inplace=True)
        return df[["datetime", "open", "high", "low", "close", "volume"]]

    def _format_symbol(self, symbol: str) -> str:
        if symbol.startswith("sh"):
            return f"{symbol[2:]}.SH"
        elif symbol.startswith("sz"):
            return f"{symbol[2:]}.SZ"
        else:
            if symbol.startswith(("6", "9")):
                return f"{symbol}.SH"
            else:
                return f"{symbol}.SZ"


class BaostockSource(DataSource):
    def get_daily(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        import baostock as bs

        bs.login()
        code = symbol.replace("sh", "").replace("sz", "")
        if not code.startswith("sh.") and not code.startswith("sz."):
            code = f"sh.{code}" if code.startswith("6") else f"sz.{code}"

        rs = bs.query_history_k_data_plus(
            code, "date,open,high,low,close,volume",
            start_date=start, end_date=end,
            frequency="d", adjustflag="3"
        )

        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        bs.logout()

        df = pd.DataFrame(data_list, columns=["datetime", "open", "high", "low", "close", "volume"])
        df = df[df["close"] != ""]
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.sort_values("datetime", inplace=True)
        return df[["datetime", "open", "high", "low", "close", "volume"]]

    def get_minute(self, symbol: str, start: str, end: str, period: str = "5") -> pd.DataFrame:
        import baostock as bs

        bs.login()
        code = symbol.replace("sh", "").replace("sz", "")
        if not code.startswith("sh.") and not code.startswith("sz."):
            code = f"sh.{code}" if code.startswith("6") else f"sz.{code}"

        freq_map = {"5": "5", "15": "15", "30": "30", "60": "60"}
        freq = freq_map.get(period, "5")

        rs = bs.query_history_k_data_plus(
            code,
            "date,time,open,high,low,close,volume",
            start_date=start,
            end_date=end,
            frequency=freq,
            adjustflag="3"
        )

        data_list = []
        while rs.error_code == '0' and rs.next():
            data_list.append(rs.get_row_data())
        bs.logout()

        if not data_list:
            return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(data_list, columns=["date", "time", "open", "high", "low", "close", "volume"])
        df = df[df["close"] != ""]
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"].str[:2] + ":" + df["time"].str[2:4] + ":" + df["time"].str[4:6])
        df.sort_values("datetime", inplace=True)
        return df[["datetime", "open", "high", "low", "close", "volume"]]


def create_data_source(source_type: str = "akshare", **kwargs) -> DataSource:
    source_type = source_type.lower()
    if source_type == "akshare":
        return AkshareSource()
    elif source_type == "tushare":
        token = kwargs.get("token")
        if not token:
            raise ValueError("使用 tushare 必须提供 token")
        return TushareSource(token)
    elif source_type == "baostock":
        return BaostockSource()
    else:
        raise ValueError(f"不支持的数据源类型: {source_type}")