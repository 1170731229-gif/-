import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantplus import QuantPlus, DailyT0Strategy, GridT0Strategy, VolatilityT0Strategy, run_backtest


class QuantPlusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QuantPlus 量化交易工具 v0.1")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.qp = None
        self.data = None

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="股票代码:", font=("微软雅黑", 11)).grid(row=0, column=0, sticky="w", pady=5)
        self.symbol_entry = ttk.Entry(main_frame, width=15, font=("微软雅黑", 11))
        self.symbol_entry.insert(0, "002475")
        self.symbol_entry.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="数据源:", font=("微软雅黑", 11)).grid(row=0, column=2, sticky="w", pady=5, padx=(20,0))
        self.source_var = tk.StringVar(value="baostock")
        ttk.Radiobutton(main_frame, text="Baostock", variable=self.source_var, value="baostock").grid(row=0, column=3, sticky="w")
        ttk.Radiobutton(main_frame, text="Akshare", variable=self.source_var, value="akshare").grid(row=0, column=4, sticky="w")

        ttk.Label(main_frame, text="数据级别:", font=("微软雅黑", 11)).grid(row=1, column=0, sticky="w", pady=5)
        self.period_var = tk.StringVar(value="5")
        ttk.Radiobutton(main_frame, text="日线", variable=self.period_var, value="daily").grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(main_frame, text="5分钟", variable=self.period_var, value="5").grid(row=1, column=2, sticky="w")
        ttk.Radiobutton(main_frame, text="15分钟", variable=self.period_var, value="15").grid(row=1, column=3, sticky="w")
        ttk.Radiobutton(main_frame, text="30分钟", variable=self.period_var, value="30").grid(row=1, column=4, sticky="w")

        ttk.Label(main_frame, text="初始资金:", font=("微软雅黑", 11)).grid(row=2, column=0, sticky="w", pady=5)
        self.cash_entry = ttk.Entry(main_frame, width=15, font=("微软雅黑", 11))
        self.cash_entry.insert(0, "20000")
        self.cash_entry.grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="策略:", font=("微软雅黑", 11)).grid(row=3, column=0, sticky="w", pady=5)
        self.strategy_var = tk.StringVar(value="DailyT0Strategy")
        strategy_frame = ttk.Frame(main_frame)
        strategy_frame.grid(row=3, column=1, columnspan=4, sticky="w")
        ttk.Radiobutton(strategy_frame, text="每日做T", variable=self.strategy_var, value="DailyT0Strategy").pack(side="left")
        ttk.Radiobutton(strategy_frame, text="网格做T", variable=self.strategy_var, value="GridT0Strategy").pack(side="left", padx=10)
        ttk.Radiobutton(strategy_frame, text="波动率做T", variable=self.strategy_var, value="VolatilityT0Strategy").pack(side="left")

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=5, pady=15)

        self.fetch_btn = ttk.Button(btn_frame, text="获取数据", command=self.fetch_data, width=12)
        self.fetch_btn.pack(side="left", padx=5)

        self.backtest_btn = ttk.Button(btn_frame, text="运行回测", command=self.run_backtest, width=12, state="disabled")
        self.backtest_btn.pack(side="left", padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="清空", command=self.clear_output, width=12)
        self.clear_btn.pack(side="left", padx=5)

        ttk.Separator(main_frame, orient="horizontal").grid(row=5, column=0, columnspan=5, sticky="ew", pady=10)

        ttk.Label(main_frame, text="输出:", font=("微软雅黑", 11)).grid(row=6, column=0, sticky="nw", pady=5)

        self.output_text = scrolledtext.ScrolledText(main_frame, width=80, height=25, font=("Consolas", 10))
        self.output_text.grid(row=7, column=0, columnspan=5, sticky="nsew", pady=5)
        main_frame.rowconfigure(7, weight=1)

        self.log("=" * 50)
        self.log("QuantPlus 量化交易工具")
        self.log("=" * 50)
        self.log("请输入股票代码，点击「获取数据」开始")
        self.log("-" * 50)

    def log(self, msg):
        self.output_text.insert("end", msg + "\n")
        self.output_text.see("end")
        self.root.update()

    def fetch_data(self):
        symbol = self.symbol_entry.get().strip()
        if not symbol:
            messagebox.showwarning("警告", "请输入股票代码")
            return

        self.fetch_btn.config(state="disabled")
        self.backtest_btn.config(state="disabled")
        self.log(f"\n正在获取 {symbol} 数据...")

        def fetch_thread():
            try:
                source = self.source_var.get()
                self.qp = QuantPlus(source)
                period = self.period_var.get()

                if period == "daily":
                    self.data = self.qp.fetch(symbol)
                    self.log(f"日线数据: {len(self.data)} 条")
                else:
                    self.data = self.qp.fetch_minute(symbol, period=period, days=30)
                    self.log(f"{period}分钟数据: {len(self.data)} 条")

                if len(self.data) > 0:
                    self.log(f"时间范围: {self.data['datetime'].min()} 至 {self.data['datetime'].max()}")
                    self.log(f"最新价: {self.data['close'].iloc[-1]:.2f}")
                    self.log("数据获取成功！可以运行回测")
                    self.root.after(0, lambda: self.backtest_btn.config(state="normal"))
                else:
                    self.log("警告: 未获取到数据")

            except Exception as e:
                self.log(f"错误: {str(e)}")
            finally:
                self.root.after(0, lambda: self.fetch_btn.config(state="normal"))

        threading.Thread(target=fetch_thread, daemon=True).start()

    def run_backtest(self):
        if self.data is None or len(self.data) == 0:
            messagebox.showwarning("警告", "请先获取数据")
            return

        try:
            cash = float(self.cash_entry.get())
        except:
            messagebox.showwarning("警告", "请输入有效的初始资金")
            return

        strategy_name = self.strategy_var.get()
        strategy_map = {
            "DailyT0Strategy": DailyT0Strategy,
            "GridT0Strategy": GridT0Strategy,
            "VolatilityT0Strategy": VolatilityT0Strategy
        }
        strategy = strategy_map[strategy_name]

        self.backtest_btn.config(state="disabled")
        self.log(f"\n{'='*50}")
        self.log(f"运行回测: {strategy_name}")
        self.log(f"初始资金: {cash} 元")
        self.log(f"{'='*50}")

        def backtest_thread():
            try:
                import io
                from contextlib import redirect_stdout

                old_stdout = sys.stdout
                sys.stdout = captured = io.StringIO()

                results = run_backtest(strategy, self.data, initial_cash=cash, commission=0.001)

                output = captured.getvalue()
                sys.stdout = old_stdout

                self.log(output)

                final_value = results[0].broker.getvalue()
                profit = final_value - cash
                profit_pct = profit / cash * 100

                self.log(f"\n{'='*50}")
                self.log(f"回测结果")
                self.log(f"{'='*50}")
                self.log(f"初始资金: {cash:.2f} 元")
                self.log(f"最终资金: {final_value:.2f} 元")
                self.log(f"收益: {profit:.2f} 元 ({profit_pct:+.2f}%)")
                self.log(f"{'='*50}")

            except Exception as e:
                self.log(f"回测错误: {str(e)}")
            finally:
                self.root.after(0, lambda: self.backtest_btn.config(state="normal"))

        threading.Thread(target=backtest_thread, daemon=True).start()

    def clear_output(self):
        self.output_text.delete("1.0", "end")
        self.log("输出已清空")


def main():
    root = tk.Tk()
    app = QuantPlusApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()