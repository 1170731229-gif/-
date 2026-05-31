import backtrader as bt
import pandas as pd
import numpy as np


def to_lot(size):
    """转换为整手（必须是100的整数倍）"""
    return int(size // 100 * 100)


class EnhancedT0Strategy(bt.Strategy):
    """
    增强型做T策略
    结合正T/反T、均价线战法、MACD背离判断
    - 正T: 先买后卖，适用于判断先跌后涨
    - 反T: 先卖后买，适用于判断先涨后跌
    - 严格仓位控制: 单次做T不超过底仓的1/3~1/2
    - 止损机制: 方向错误及时止损
    """

    params = (
        ("base_shares", 100),        # 底仓股数（必须是100整数倍）
        ("t_ratio", 0.33),           # 做T仓位比例（不超过底仓1/3）
        ("price_range", 0.015),     # 价格波动阈值（1.5%，覆盖手续费）
        ("stop_loss", 0.005),       # 止损线（-0.5%）
        ("use_avg_line", True),      # 是否使用均价线判断
        ("use_macd_div", True),      # 是否使用MACD背离
        ("verbose", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datalow = self.datas[0].low
        self.datahigh = self.datas[0].high
        self.volume = self.datas[0].volume

        self.order = None
        self.base_shares = self.params.base_shares
        self.has_base = False
        self.last_day = None

        # T仓持仓（正T买入手数）
        self.t_long = 0
        # T仓持仓（反T卖出手数）
        self.t_short = 0
        # 今日做T次数限制
        self.t_count = 0
        self.max_t_per_day = 2

        # MACD计算
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        # 均价线缓存
        self.vwap_history = []

    def log(self, txt, dt=None):
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"[买入] 价格:{order.executed.price:.2f} 数量:{order.executed.size}")
            else:
                self.log(f"[卖出] 价格:{order.executed.price:.2f} 数量:{order.executed.size}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("[订单] 取消/拒绝")
        self.order = None

    def next(self):
        current_day = self.datas[0].datetime.date(0)

        # 新的一天：初始化
        if self.last_day != current_day:
            if not self.has_base:
                # 首日建仓
                self.order = self.buy(size=self.base_shares)
                self.has_base = True
                self.log(f"[建仓] 底仓{self.base_shares}股 开盘价:{self.dataopen[0]:.2f}")
            else:
                # 新交易日开始
                self.t_long = 0
                self.t_short = 0
                self.t_count = 0
                self.vwap_history = []
            self.last_day = current_day

        if self.order:
            return

        # 获取当前持仓
        position = self.getposition().size
        open_price = self.dataopen[0]
        close_price = self.dataclose[0]
        high_price = self.datahigh[0]
        low_price = self.datalow[0]

        # 计算均价线(VWAP)
        vwap = self._calculate_vwap()

        # 计算日内波动
        drop_from_open = (open_price - low_price) / open_price
        rise_from_open = (high_price - open_price) / open_price

        # 正T逻辑: 先买后卖
        # 条件: 股价在均价线下方 + 下跌超过阈值 + 未超过做T次数 + 有可用资金
        if self.t_count < self.max_t_per_day:
            # 正T买入条件
            if self.t_long == 0 and position >= self.base_shares:
                can_buy = self._can_buy_t()
                if can_buy and drop_from_open >= self.params.price_range:
                    # 检查是否在均价线下方
                    if not self.params.use_avg_line or close_price < vwap:
                        # 检查MACD底背离（可选）
                        if not self.params.use_macd_div or self._check_bottom_divergence():
                            t_shares = to_lot(int(self.base_shares * self.params.t_ratio))
                            if t_shares >= 100:
                                self.log(f"[正T买入] 下跌{drop_from_open*100:.1f}% 均价线{'下方' if close_price<vwap else '上方'} 买入{t_shares}股")
                                self.order = self.buy(size=t_shares)
                                self.t_long = t_shares
                                self.t_count += 1
                                return

            # 正T卖出条件: 有正T持仓且价格上涨
            if self.t_long > 0 and rise_from_open >= self.params.price_range:
                # 卖出等量正T买入的仓位
                self.log(f"[正T卖出] 上涨{rise_from_open*100:.1f}% 卖出{self.t_long}股")
                self.order = self.sell(size=self.t_long)
                profit = (close_price - open_price) * self.t_long
                self.log(f"[正T利润] {profit:.2f}元")
                self.t_long = 0
                return

            # 反T卖出条件: 先卖后买
            if self.t_short == 0 and position >= self.base_shares:
                # 股价在均价线上方 + 上涨超过阈值
                if (not self.params.use_avg_line or close_price > vwap) and rise_from_open >= self.params.price_range:
                    # 检查MACD顶背离（可选）
                    if not self.params.use_macd_div or self._check_top_divergence():
                        t_shares = to_lot(int(self.base_shares * self.params.t_ratio))
                        if t_shares >= 100:
                            self.log(f"[反T卖出] 上涨{rise_from_open*100:.1f}% 均价线{'上方' if close_price>vwap else '下方'} 卖出{t_shares}股")
                            self.order = self.sell(size=t_shares)
                            self.t_short = t_shares
                            self.t_count += 1
                            return

            # 反T买回条件: 有反T卖出持仓且价格回落
            if self.t_short > 0 and drop_from_open >= self.params.price_range:
                self.log(f"[反T买回] 下跌{drop_from_open*100:.1f}% 买回{self.t_short}股")
                self.order = self.buy(size=self.t_short)
                profit = (open_price - close_price) * self.t_short
                self.log(f"[反T利润] {profit:.2f}元")
                self.t_short = 0
                return

        # 止损逻辑: 正T买入后继续下跌
        if self.t_long > 0:
            stop_price = open_price * (1 - self.params.stop_loss)
            if close_price < stop_price:
                self.log(f"[正T止损] 价格{close_price:.2f}<止损价{stop_price:.2f} 卖出{self.t_long}股")
                self.order = self.sell(size=self.t_long)
                self.t_long = 0
                return

        # 收盘前处理: 平掉所有T仓
        if len(self.datas[0]) >= 50:  # 收盘前约30分钟
            if self.t_long > 0:
                self.log(f"[收盘平仓] 卖出正T仓位{self.t_long}股")
                self.order = self.sell(size=self.t_long)
                self.t_long = 0
            if self.t_short > 0:
                self.log(f"[收盘平仓] 买回反T仓位{self.t_short}股")
                self.order = self.buy(size=self.t_short)
                self.t_short = 0

    def _calculate_vwap(self):
        """计算均价线"""
        typical_price = (self.datahigh[0] + self.datalow[0] + self.dataclose[0]) / 3
        cum_volume = self.volume[0]
        if cum_volume > 0:
            self.vwap_history.append((typical_price, cum_volume))

        if len(self.vwap_history) == 0:
            return self.dataclose[0]

        total_volume = sum(v for _, v in self.vwap_history)
        if total_volume == 0:
            return self.dataclose[0]

        vwap = sum(p * v for p, v in self.vwap_history) / total_volume
        return vwap

    def _can_buy_t(self):
        """检查是否有足够的资金做正T"""
        buy_amount = self.dataclose[0] * int(self.base_shares * self.params.t_ratio)
        return self.broker.getcash() >= buy_amount

    def _check_bottom_divergence(self):
        """检查MACD底背离"""
        if len(self.dataclose) < 35:
            return True

        close_prices = self.dataclose.get(size=35)
        ema_fast = pd.Series(close_prices).ewm(span=12, adjust=False).mean()
        ema_slow = pd.Series(close_prices).ewm(span=26, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_hist = 2 * (dif - dea)

        if len(macd_hist) < 5:
            return True

        recent_low_price = min(close_prices[-5:])
        old_low_price = min(close_prices[-15:-5])
        recent_low_macd = min(macd_hist[-5:])
        old_low_macd = min(macd_hist[-15:-5])

        return recent_low_price < old_low_price and recent_low_macd > old_low_macd

    def _check_top_divergence(self):
        """检查MACD顶背离"""
        if len(self.dataclose) < 35:
            return True

        close_prices = self.dataclose.get(size=35)
        ema_fast = pd.Series(close_prices).ewm(span=12, adjust=False).mean()
        ema_slow = pd.Series(close_prices).ewm(span=26, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_hist = 2 * (dif - dea)

        if len(macd_hist) < 5:
            return True

        recent_high_price = max(close_prices[-5:])
        old_high_price = max(close_prices[-15:-5])
        recent_high_macd = max(macd_hist[-5:])
        old_high_macd = max(macd_hist[-15:-5])

        return recent_high_price > old_high_price and recent_high_macd < old_high_macd

    def stop(self):
        """策略结束时平仓"""
        pos = self.getposition().size
        if pos > 0:
            self.order = self.sell(size=pos)
            self.log(f"[策略结束] 平仓卖出{pos}股")


class GridT0StrategyAdvanced(bt.Strategy):
    """
    高级网格做T策略
    - 预设价格网格，跌破买入，涨破卖出
    - 每次只做底仓的1/3~1/2
    - 严格按网格执行，适合震荡市
    """

    params = (
        ("base_shares", 100),
        ("grid_pct", 0.01),         # 网格间距1%
        ("t_ratio", 0.33),          # 每格做T仓位比例
        ("max_grids", 10),           # 最大网格数
        ("verbose", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.base_price = None
        self.grid_positions = {}     # 各网格持仓
        self.last_day = None
        self.total_profit = 0

    def log(self, txt, dt=None):
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"[买入] 价格:{order.executed.price:.2f} 数量:{order.executed.size}")
            else:
                self.log(f"[卖出] 价格:{order.executed.price:.2f} 数量:{order.executed.size}")
        self.order = None

    def next(self):
        current_day = self.datas[0].datetime.date(0)

        if self.last_day != current_day:
            if self.base_price is None:
                self.base_price = self.dataclose[0]
                self.log(f"[网格初始化] 基准价:{self.base_price:.2f} 间距:{self.params.grid_pct*100}%")
            else:
                self.grid_positions = {}
            self.last_day = current_day

        if self.order:
            return

        price = self.dataclose[0]
        grid_step = self.base_price * self.params.grid_pct

        for i in range(1, self.params.max_grids):
            buy_price = self.base_price - i * grid_step
            sell_price = self.base_price + i * grid_step

            # 触发买入网格
            if price <= buy_price and self.grid_positions.get(-i, 0) == 0:
                t_shares = to_lot(int(self.params.base_shares * self.params.t_ratio))
                if t_shares >= 100:
                    self.log(f"[网格{i}买入] 价格{price:.2f}<={buy_price:.2f} 买入{t_shares}股")
                    self.order = self.buy(size=t_shares)
                    self.grid_positions[-i] = t_shares
                    break

            # 触发卖出网格
            if price >= sell_price and self.grid_positions.get(i, 0) == 0:
                t_shares = to_lot(int(self.params.base_shares * self.params.t_ratio))
                if t_shares >= 100:
                    self.log(f"[网格{i}卖出] 价格{price:.2f}>={sell_price:.2f} 卖出{t_shares}股")
                    self.order = self.sell(size=t_shares)
                    self.grid_positions[i] = t_shares
                    break


class TrendT0Strategy(bt.Strategy):
    """
    趋势跟踪做T策略
    - 判断日内趋势方向
    - 顺势做T：上升趋势做正T，下降趋势做反T
    - 趋势判断：EMA均线
    """

    params = (
        ("base_shares", 100),
        ("t_ratio", 0.33),
        ("ema_period", 20),          # EMA周期
        ("trend_threshold", 0.005),  # 趋势确认阈值
        ("verbose", True),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datalow = self.datas[0].low
        self.datahigh = self.datas[0].high

        self.order = None
        self.base_shares = self.params.base_shares
        self.has_base = False
        self.last_day = None

        self.t_long = 0
        self.t_short = 0
        self.t_count = 0
        self.max_t_per_day = 2

        self.trend = 0  # 1=上涨, -1=下跌, 0=震荡

    def log(self, txt, dt=None):
        if self.params.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f"[买入] 价格:{order.executed.price:.2f} 数量:{order.executed.size}")
            else:
                self.log(f"[卖出] 价格:{order.executed.price:.2f} 数量:{order.executed.size}")
        self.order = None

    def next(self):
        current_day = self.datas[0].datetime.date(0)

        if self.last_day != current_day:
            if not self.has_base:
                self.order = self.buy(size=self.base_shares)
                self.has_base = True
                self.log(f"[建仓] 底仓{self.base_shares}股")
            else:
                self.t_long = 0
                self.t_short = 0
                self.t_count = 0
            self.last_day = current_day

        if self.order:
            return

        position = self.getposition().size
        price = self.dataclose[0]
        open_price = self.dataopen[0]
        high = self.datahigh[0]
        low = self.datalow[0]

        # 计算EMA判断趋势
        if len(self.dataclose) >= self.params.ema_period:
            ema = pd.Series(self.dataclose.get(size=self.params.ema_period)).ewm(span=self.params.ema_period, adjust=False).mean().iloc[-1]
            price_ema_diff = (price - ema) / ema

            if price_ema_diff > self.params.trend_threshold:
                self.trend = 1
            elif price_ema_diff < -self.params.trend_threshold:
                self.trend = -1
            else:
                self.trend = 0

        if self.t_count < self.max_t_per_day:
            drop = (open_price - low) / open_price
            rise = (high - open_price) / open_price

            # 上涨趋势: 正T
            if self.trend == 1 and self.t_long == 0 and position >= self.base_shares:
                if drop >= 0.01:
                    t_shares = to_lot(int(self.base_shares * self.params.t_ratio))
                    if t_shares >= 100:
                        self.log(f"[趋势做T-正T] 上涨趋势 下跌{drop*100:.1f}% 买入{t_shares}股")
                        self.order = self.buy(size=t_shares)
                        self.t_long = t_shares
                        self.t_count += 1

            elif self.t_long > 0 and rise >= 0.01:
                self.log(f"[趋势做T-正T卖出] 上涨{rise*100:.1f}% 卖出{self.t_long}股")
                self.order = self.sell(size=self.t_long)
                self.t_long = 0

            # 下跌趋势: 反T
            elif self.trend == -1 and self.t_short == 0 and position >= self.base_shares:
                if rise >= 0.01:
                    t_shares = to_lot(int(self.base_shares * self.params.t_ratio))
                    if t_shares >= 100:
                        self.log(f"[趋势做T-反T] 下跌趋势 上涨{rise*100:.1f}% 卖出{t_shares}股")
                        self.order = self.sell(size=t_shares)
                        self.t_short = t_shares
                        self.t_count += 1

            elif self.t_short > 0 and drop >= 0.01:
                self.log(f"[趋势做T-反T买回] 下跌{drop*100:.1f}% 买回{self.t_short}股")
                self.order = self.buy(size=self.t_short)
                self.t_short = 0

        # 收盘平仓
        if len(self.datas[0]) >= 50:
            if self.t_long > 0:
                self.order = self.sell(size=self.t_long)
                self.t_long = 0
            if self.t_short > 0:
                self.order = self.buy(size=self.t_short)
                self.t_short = 0

    def stop(self):
        pos = self.getposition().size
        if pos > 0:
            self.order = self.sell(size=pos)
            self.log(f"[策略结束] 平仓卖出{pos}股")