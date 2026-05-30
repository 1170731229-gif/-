"""
机器学习策略模块 - 基于Backtrader的ML策略
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Optional, Any, List
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression


class MLStrategy(bt.Strategy):
    """机器学习策略基类"""
    params = (
        ("model", None),
        ("feature_cols", None),
        ("lookback", 20),
        ("predict_threshold", 0.5),
        ("position_size", 1.0),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
        self.feature_history = []
        self.price_history = []
        self.signal = None
        
        if self.params.model is None:
            self.params.model = LogisticRegression()
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} - {txt}")
    
    def append_history(self):
        features = self._extract_features()
        self.feature_history.append(features)
        self.price_history.append({
            "close": self.dataclose[0],
            "high": self.datas[0].high[0],
            "low": self.datas[0].low[0],
            "volume": self.datavolume[0],
        })
        
        if len(self.feature_history) > self.params.lookback * 2:
            self.feature_history.pop(0)
            self.price_history.pop(0)
    
    def _extract_features(self) -> dict:
        """从当前历史窗口提取特征"""
        features = {}
        
        if len(self.price_history) < 5:
            return features
        
        closes = [p["close"] for p in self.price_history]
        volumes = [p["volume"] for p in self.price_history]
        
        if self.params.feature_cols is None:
            features["return_1"] = (closes[-1] / closes[-2] - 1) if len(closes) >= 2 else 0
            features["return_5"] = (closes[-1] / closes[-6] - 1) if len(closes) >= 6 else 0
            features["volatility_5"] = np.std(closes[-5:]) / np.mean(closes[-5:]) if len(closes) >= 5 else 0
            features["volume_ratio"] = volumes[-1] / np.mean(volumes[-5:]) if len(volumes) >= 5 else 1
            features["ma5"] = np.mean(closes[-5:]) / closes[-1] if len(closes) >= 5 else 1
            features["ma20"] = np.mean(closes[-20:]) / closes[-1] if len(closes) >= 20 else 1
        else:
            for col in self.params.feature_cols:
                if col in self.feature_history[-1]:
                    features[col] = self.feature_history[-1][col]
        
        return features
    
    def _prepare_training_data(self) -> tuple:
        """准备训练数据"""
        if len(self.feature_history) < self.params.lookback + 5:
            return None, None
        
        X = []
        y = []
        
        for i in range(self.params.lookback, len(self.feature_history) - 1):
            if isinstance(self.feature_history[i], dict) and self.feature_history[i]:
                X.append(list(self.feature_history[i].values()))
                next_return = (self.price_history[i + 1]["close"] / 
                             self.price_history[i]["close"] - 1)
                y.append(1 if next_return > 0 else 0)
        
        return np.array(X), np.array(y)
    
    def _train_model(self):
        """训练模型"""
        X, y = self._prepare_training_data()
        if X is None or len(X) < 30:
            return
        
        try:
            self.params.model.fit(X, y)
            self.signal = "trained"
        except Exception as e:
            self.signal = f"error: {e}"
    
    def _predict(self) -> Optional[float]:
        """预测"""
        if len(self.feature_history) < self.params.lookback:
            return None
        
        current_features = self.feature_history[-1]
        if not isinstance(current_features, dict) or not current_features:
            return None
        
        try:
            X = np.array([list(current_features.values())])
            prob = self.params.model.predict_proba(X)[0][1]
            return prob
        except Exception:
            return None
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price:.2f}, "
                        f"Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            else:
                self.log(f"SELL EXECUTED, Price: {order.executed.price:.2f}, "
                        f"Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}")
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
        
        self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f"TRADE PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}")
    
    def next(self):
        self.append_history()
        
        if len(self.feature_history) == self.params.lookback:
            self._train_model()
        
        if self.signal != "trained":
            return
        
        prob = self._predict()
        if prob is None:
            return
        
        if not self.position:
            if prob > self.params.predict_threshold:
                self.log(f"Signal: BUY, Prob: {prob:.4f}")
                self.order = self.buy()
        else:
            if prob < (1 - self.params.predict_threshold):
                self.log(f"Signal: SELL, Prob: {prob:.4f}")
                self.order = self.sell()


def create_ml_strategy(
    model: Any = None,
    feature_cols: List[str] = None,
    lookback: int = 20,
    predict_threshold: float = 0.5
) -> type:
    """创建ML策略类"""
    if model is None:
        model = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
    
    class CustomMLStrategy(MLStrategy):
        pass
    
    CustomMLStrategy.params = (
        ("model", model),
        ("feature_cols", feature_cols),
        ("lookback", lookback),
        ("predict_threshold", predict_threshold),
        ("position_size", 1.0),
    )
    
    return CustomMLStrategy


def run_ml_backtest(
    df: pd.DataFrame,
    model: Any = None,
    initial_cash: float = 100000,
    commission: float = 0.001,
    lookback: int = 20
):
    """运行ML策略回测"""
    import backtrader as bt
    
    if model is None:
        model = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
    
    StrategyClass = create_ml_strategy(model=model, lookback=lookback)
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(StrategyClass)
    
    df = df.copy()
    df.set_index("date", inplace=True)
    data = bt.feeds.PandasData(dataname=df)
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