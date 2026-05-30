import backtrader as bt
import pandas as pd


def to_lot(size):
    """转换为整手（必须是100的整数倍）"""
    return int(size // 100 * 100)


class DailyT0Strategy(bt.Strategy):
    """
    每日做T策略
    - 底仓模式：先持有股票，当日内价格下跌时买入，上涨时卖出
    - 收盘前平仓，保持原有持仓不变
    - 手数必须是100的整数倍
    """

    params = (
        ("stock_size", 100),        # 底仓股数（必须是100的整数倍）
        ("t_range", 0.02),         # 做T价格区间（2%波动）
        ("buy_ratio", 0.5),         # 下跌时买入底仓的比例
        ("sell_ratio", 0.5),        # 上涨时卖出的比例
        ("close_minutes", 14),      # 收盘前多少分钟平仓
        ("verbose", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datalow = self.datas[0].low
        self.datahigh = self.datas[0].high
        self.volume = self.datas[0].volume

        self.order = None
        self.t_position = 0
        self.base_position = 0
        self.has_base = False
        self.last_day = None

    def log(self, txt, dt=None):
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"买入, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}")
            else:
                self.log(f"卖出, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("订单被取消/保证金不足/拒绝")
        self.order = None

    def next(self):
        current_day = self.datas[0].datetime.date(0)

        if self.last_day != current_day:
            if not self.has_base:
                size = to_lot(self.params.stock_size)
                self.order = self.buy(size=size)
                self.base_position = size
                self.has_base = True
                self.log(f"建仓底仓 {size} 股, 开盘价: {self.dataopen[0]:.2f}")
            else:
                self.t_position = 0
            self.last_day = current_day

        if self.order:
            return

        open_price = self.dataopen[0]
        low_price = self.datalow[0]
        high_price = self.datahigh[0]

        drop_ratio = (open_price - low_price) / open_price
        rise_ratio = (high_price - open_price) / open_price

        if self.t_position >= 0 and drop_ratio >= self.params.t_range:
            buy_size = to_lot(int(self.base_position * self.params.buy_ratio))
            if buy_size >= 100:
                self.log(f"做T买入信号, 下跌{drop_ratio*100:.1f}%, 买入{buy_size}股")
                self.order = self.buy(size=buy_size)
                self.t_position += buy_size

        elif self.t_position <= 0 and rise_ratio >= self.params.t_range:
            sell_size = to_lot(int(self.base_position * self.params.sell_ratio))
            if sell_size >= 100:
                self.log(f"做T卖出信号, 上涨{rise_ratio*100:.1f}%, 卖出{sell_size}股")
                self.order = self.sell(size=sell_size)
                self.t_position -= sell_size

        if len(self.datas[0]) >= 60:
            remaining = self.getposition().size - self.base_position
            if remaining != 0:
                close_size = to_lot(abs(remaining))
                if close_size >= 100:
                    self.log(f"收盘平仓, {'卖出' if remaining > 0 else '买入'}{close_size}股")
                    if remaining > 0:
                        self.order = self.sell(size=close_size)
                    else:
                        self.order = self.buy(size=close_size)
                    self.t_position = 0

    def stop(self):
        pos = self.getposition().size
        if pos > 0:
            close_size = to_lot(pos)
            self.order = self.sell(size=close_size)
            self.log(f"策略结束, 平仓卖出 {close_size} 股")
        elif pos < 0:
            close_size = to_lot(-pos)
            self.order = self.buy(size=close_size)
            self.log(f"策略结束, 平仓买入 {close_size} 股")


class GridT0Strategy(bt.Strategy):
    """
    网格做T策略
    - 设置价格网格，跌破网格买入，涨破网格卖出
    """

    params = (
        ("grid_count", 10),
        ("position_pct", 0.5),
        ("base_price", None),
        ("verbose", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.order = None
        self.base_price = None
        self.grid_size = None
        self.positions = {}
        self.last_day = None

    def log(self, txt, dt=None):
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"买入, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}")
            else:
                self.log(f"卖出, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}")
        self.order = None

    def next(self):
        current_day = self.datas[0].datetime.date(0)

        if self.last_day != current_day:
            if self.base_price is None:
                self.base_price = self.dataopen[0]
                self.grid_size = self.base_price / self.params.grid_count
                self.log(f"网格初始化, 基准价: {self.base_price:.2f}, 网格间距: {self.grid_size:.2f}")
            self.last_day = current_day

        if self.order:
            return

        close_price = self.dataclose[0]

        for i in range(1, self.params.grid_count):
            grid_price = self.base_price - i * self.grid_size
            if close_price <= grid_price and self.positions.get(i, 0) == 0:
                size = to_lot(int(100 * self.params.position_pct))
                if size >= 100:
                    self.log(f"网格{i}买入, 价格{close_price:.2f} <= {grid_price:.2f}, 买入{size}股")
                    self.order = self.buy(size=size)
                    self.positions[i] = size
                    break

        for i in range(1, self.params.grid_count):
            grid_price = self.base_price - i * self.grid_size
            if close_price >= grid_price and self.positions.get(i, 0) > 0:
                size = to_lot(self.positions[i])
                if size >= 100:
                    self.log(f"网格{i}卖出, 价格{close_price:.2f} >= {grid_price:.2f}, 卖出{size}股")
                    self.order = self.sell(size=size)
                    self.positions[i] = 0
                    break


class VolatilityT0Strategy(bt.Strategy):
    """
    波动率做T策略
    - 根据日内波动率动态调整做T仓位
    """

    params = (
        ("lookback", 20),
        ("vol_threshold", 0.015),
        ("size", 100),
        ("verbose", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datalow = self.datas[0].low
        self.datahigh = self.datas[0].high
        self.order = None
        self.t_count = 0
        self.last_day = None
        self.daily_volatility = 0.02

    def log(self, txt, dt=None):
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"买入, 价格: {order.executed.price:.2f}")
            else:
                self.log(f"卖出, 价格: {order.executed.price:.2f}")
        self.order = None

    def next(self):
        current_day = self.datas[0].datetime.date(0)

        if self.last_day != current_day:
            self.t_count = 0
            self.last_day = current_day

            if len(self.dataclose) >= self.params.lookback:
                returns = pd.Series(self.dataclose.get(size=self.params.lookback)).pct_change().dropna()
                self.daily_volatility = returns.std()
                self.log(f"日波动率: {self.daily_volatility*100:.2f}%")

        if self.order:
            return

        open_price = self.dataopen[0]
        low_price = self.datalow[0]
        high_price = self.datahigh[0]

        if self.daily_volatility > self.params.vol_threshold:
            drop_ratio = (open_price - low_price) / open_price
            rise_ratio = (high_price - open_price) / open_price

            if drop_ratio >= 0.01 and self.t_count == 0:
                size = to_lot(self.params.size)
                if size >= 100:
                    self.log(f"波动做T买入, 下跌{drop_ratio*100:.2f}%")
                    self.order = self.buy(size=size)
                    self.t_count = 1

            elif rise_ratio >= 0.01 and self.t_count == 1:
                size = to_lot(self.params.size)
                if size >= 100:
                    self.log(f"波动做T卖出, 上涨{rise_ratio*100:.2f}%")
                    self.order = self.sell(size=size)
                    self.t_count = 0

        if len(self.datas[0]) >= 60 and self.t_count > 0:
            self.log("收盘前平仓")
            size = to_lot(self.params.size)
            self.order = self.sell(size=size)
            self.t_count = 0