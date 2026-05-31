import backtrader as bt
import pandas as pd

class StrategyTemplate(bt.Strategy):
    params = ()

    def __init__(self):
        self.dataclose = self.datas[0].close

    def next(self):
        pass

def run_backtest(strategy_class, df: pd.DataFrame,
                 initial_cash=100000, commission=0.001):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)

    df_copy = df.copy()
    if "date" in df_copy.columns:
        df_copy.set_index("date", inplace=True)
    elif "datetime" in df_copy.columns:
        df_copy.set_index("datetime", inplace=True)

    data = bt.feeds.PandasData(dataname=df_copy)
    cerebro.adddata(data)
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    print(f"初始资金: {cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    print(f"最终资金: {cerebro.broker.getvalue():.2f}")
    return results