import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_candlestick(df: pd.DataFrame, indicators: dict = None, title="Stock"):
    """df 需包含 date, open, high, low, close, volume"""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.02)

    fig.add_trace(go.Candlestick(x=df["date"],
                                 open=df["open"], high=df["high"],
                                 low=df["low"], close=df["close"],
                                 name="Price"), row=1, col=1)

    if indicators:
        for name, values in indicators.items():
            fig.add_trace(go.Scatter(x=df["date"], y=values,
                                     mode="lines", name=name),
                          row=1, col=1)

    fig.add_trace(go.Bar(x=df["date"], y=df["volume"], name="Volume",
                         marker_color="lightgray"), row=2, col=1)

    fig.update_layout(title=title, xaxis_rangeslider_visible=False)
    return fig

def plot_matplotlib(df: pd.DataFrame, indicators=None):
    import matplotlib.pyplot as plt
    # 简化版示例
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3,1]})
    ax1.plot(df["date"], df["close"], label="Close")
    if indicators:
        for name, vals in indicators.items():
            ax1.plot(df["date"], vals, label=name)
    ax1.legend()
    ax2.bar(df["date"], df["volume"], color="gray")
    return fig