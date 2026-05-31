import pandas as pd
import numpy as np
import backtrader as bt

class MLTradingStrategy(bt.Strategy):
    params = (
        ("model", None),
        ("feature_builder", None),
        ("scaler", None),
        ("verbose", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.volume = self.datas[0].volume
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def log(self, txt, dt=None):
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"买入执行, 价格: {order.executed.price:.2f}, "
                        f"成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}")
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f"卖出执行, 价格: {order.executed.price:.2f}, "
                        f"成本: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("订单被取消/保证金不足/拒绝")
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f"交易利润, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}")

    def next(self):
        if self.order:
            return

        if len(self.datas[0]) < 20:
            return

        features = self._build_current_features()
        if features is None:
            return

        features_scaled = self.params.scaler.transform([features])
        signal = self.params.model.predict(features_scaled)[0]

        if not self.position:
            if signal == 1:
                self.log(f"买入信号, 信号值: {signal}")
                self.order = self.buy()
        else:
            if signal == 0:
                self.log(f"卖出信号, 信号值: {signal}")
                self.order = self.sell()

    def _build_current_features(self):
        try:
            close = self.dataclose.get(size=20)
            volume = self.volume.get(size=20)
            high = self.datas[0].high.get(size=20)
            low = self.datas[0].low.get(size=20)
            open_ = self.datas[0].open.get(size=20)

            if len(close) < 20:
                return None

            close_series = pd.Series(close)
            return_1d = close_series.pct_change().iloc[-1] if not pd.isna(close_series.pct_change().iloc[-1]) else 0
            return_5d = (close / close[4] - 1) if len(close) >= 5 else 0
            return_10d = (close / close[9] - 1) if len(close) >= 10 else 0
            volatility_5d = close_series.pct_change().rolling(5).std().iloc[-1] if len(close) >= 5 else 0
            volatility_20d = close_series.pct_change().rolling(20).std().iloc[-1] if len(close) >= 20 else 0
            ma5 = close_series.rolling(5).mean().iloc[-1]
            ma20 = close_series.rolling(20).mean().iloc[-1]
            ma_ratio = ma5 / ma20 if ma20 != 0 else 1
            volume_ratio = volume[-1] / np.mean(volume[-20:]) if len(volume) >= 20 else 1
            high_low_ratio = (high[-1] - low[-1]) / close[-1]
            upper_shadow = (high[-1] - max(open_[-1], close[-1])) / close[-1]
            lower_shadow = (min(open_[-1], close[-1]) - low[-1]) / close[-1]

            return [return_1d, return_5d, return_10d, volatility_5d, volatility_20d,
                    ma_ratio, volume_ratio, high_low_ratio, upper_shadow, lower_shadow]
        except Exception:
            return None

def run_ml_backtest(df: pd.DataFrame, model, scaler,
                     initial_cash: float = 100000,
                     commission: float = 0.001):
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    data_feed = bt.feeds.PandasData(
        dataname=df.set_index("date"),
        datetime=None,
        open=1, high=2, low=3, close=4, volume=5,
        openinterest=-1
    )
    cerebro.adddata(data_feed)

    cerebro.addstrategy(
        MLTradingStrategy,
        model=model,
        scaler=scaler,
        verbose=False
    )

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")

    starting_value = cerebro.broker.getvalue()
    print(f"初始资金: {starting_value:.2f}")

    results = cerebro.run()
    final_value = cerebro.broker.getvalue()

    print(f"最终资金: {final_value:.2f}")
    print(f"总收益率: {(final_value / starting_value - 1) * 100:.2f}%")

    return results