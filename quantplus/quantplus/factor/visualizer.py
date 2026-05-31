"""
因子可视化模块 - IC分析、因子有效性可视化
"""

import pandas as pd
import numpy as np
from typing import Optional, List
import matplotlib.pyplot as plt


class FactorVisualizer:
    def __init__(self, figsize: tuple = (14, 8)):
        self.figsize = figsize
        plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
    
    def plot_ic_series(
        self,
        ic_series: pd.Series,
        title: str = "IC时序图",
        save_path: Optional[str] = None
    ) -> None:
        """绘制IC时序图"""
        fig, ax = plt.subplots(figsize=(12, 4))
        
        ic_series.index = ic_series.index.astype(str)
        
        colors = ["green" if x > 0 else "red" for x in ic_series.values]
        ax.bar(range(len(ic_series)), ic_series.values, color=colors, alpha=0.7)
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax.axhline(y=ic_series.mean(), color="blue", linestyle="--", 
                   label=f"IC Mean: {ic_series.mean():.4f}")
        
        ax.set_title(title)
        ax.set_xlabel("Date")
        ax.set_ylabel("IC Value")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
    
    def plot_ic_cumulative(
        self,
        ic_series: pd.Series,
        title: str = "IC累积曲线",
        save_path: Optional[str] = None
    ) -> None:
        """绘制IC累积曲线"""
        fig, ax = plt.subplots(figsize=(12, 4))
        
        ic_cumsum = ic_series.cumsum()
        ic_cumsum.index = ic_cumsum.index.astype(str)
        
        ax.plot(range(len(ic_cumsum)), ic_cumsum.values, 
                linewidth=2, color="blue", label="Cumulative IC")
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax.fill_between(range(len(ic_cumsum)), 0, ic_cumsum.values, 
                        where=ic_cumsum.values > 0, alpha=0.3, color="green")
        ax.fill_between(range(len(ic_cumsum)), 0, ic_cumsum.values, 
                        where=ic_cumsum.values < 0, alpha=0.3, color="red")
        
        ax.set_title(title)
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative IC")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
    
    def plot_ic_distribution(
        self,
        ic_series: pd.Series,
        title: str = "IC分布直方图",
        save_path: Optional[str] = None
    ) -> None:
        """绘制IC分布直方图"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 4))
        
        axes[0].hist(ic_series.values, bins=20, edgecolor="black", alpha=0.7)
        axes[0].axvline(x=ic_series.mean(), color="red", linestyle="--",
                        label=f"Mean: {ic_series.mean():.4f}")
        axes[0].axvline(x=0, color="black", linestyle="-", linewidth=0.5)
        axes[0].set_title(f"{title} - Histogram")
        axes[0].set_xlabel("IC Value")
        axes[0].set_ylabel("Frequency")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        ic_sorted = np.sort(ic_series.values)
        cumulative = np.arange(1, len(ic_sorted) + 1) / len(ic_sorted)
        axes[1].plot(ic_sorted, cumulative, linewidth=2)
        axes[1].axvline(x=0, color="black", linestyle="-", linewidth=0.5)
        axes[1].set_title(f"{title} - CDF")
        axes[1].set_xlabel("IC Value")
        axes[1].set_ylabel("Cumulative Probability")
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
    
    def plot_quantile_returns(
        self,
        returns_df: pd.DataFrame,
        title: str = "分位数组合收益",
        save_path: Optional[str] = None
    ) -> None:
        """绘制分位数组合累计收益"""
        fig, ax = plt.subplots(figsize=(12, 5))
        
        for col in returns_df.columns:
            ax.plot(returns_df.index, returns_df[col].values, linewidth=2, label=col)
        
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax.set_title(title)
        ax.set_xlabel("Period")
        ax.set_ylabel("Cumulative Return")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
    
    def plot_ic_heatmap(
        self,
        ic_matrix: pd.DataFrame,
        title: str = "因子IC热力图",
        save_path: Optional[str] = None
    ) -> None:
        """绘制多因子IC热力图"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        im = ax.imshow(ic_matrix.values, aspect="auto", cmap="RdYlGn")
        
        ax.set_xticks(range(len(ic_matrix.columns)))
        ax.set_xticklabels(ic_matrix.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(ic_matrix.index)))
        ax.set_yticklabels([str(x) for x in ic_matrix.index])
        
        ax.set_title(title)
        
        for i in range(len(ic_matrix.index)):
            for j in range(len(ic_matrix.columns)):
                val = ic_matrix.iloc[i, j]
                if not np.isnan(val):
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                           color="black" if abs(val) < 0.5 else "white", fontsize=8)
        
        plt.colorbar(im, ax=ax, label="IC Value")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()
    
    def plot_factor_correlation(
        self,
        factor_df: pd.DataFrame,
        factor_cols: List[str],
        title: str = "因子相关性矩阵",
        save_path: Optional[str] = None
    ) -> None:
        """绘制因子相关性矩阵"""
        corr_matrix = factor_df[factor_cols].corr()
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        im = ax.imshow(corr_matrix.values, aspect="auto", cmap="coolwarm", vmin=-1, vmax=1)
        
        ax.set_xticks(range(len(factor_cols)))
        ax.set_xticklabels(factor_cols, rotation=45, ha="right")
        ax.set_yticks(range(len(factor_cols)))
        ax.set_yticklabels(factor_cols)
        
        ax.set_title(title)
        
        for i in range(len(factor_cols)):
            for j in range(len(factor_cols)):
                val = corr_matrix.iloc[i, j]
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                       color="black" if abs(val) < 0.5 else "white", fontsize=9)
        
        plt.colorbar(im, ax=ax, label="Correlation")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()


def quick_ic_analysis(
    factor_df: pd.DataFrame,
    factor_cols: List[str],
    label_col: str = "label",
    save_dir: Optional[str] = None
) -> dict:
    """快速IC分析（自动生成所有图表）"""
    from .evaluator import FactorEvaluator
    
    visualizer = FactorVisualizer()
    results = {}
    
    for col in factor_cols:
        if col not in factor_df.columns:
            continue
        
        ic_series = FactorEvaluator.calculate_ic(factor_df, col, label_col)
        
        prefix = f"{save_dir}/{col}" if save_dir else None
        
        visualizer.plot_ic_series(ic_series, title=f"{col} IC序列",
                                   save_path=f"{prefix}_ic.png" if prefix else None)
        visualizer.plot_ic_cumulative(ic_series, title=f"{col} IC累积",
                                       save_path=f"{prefix}_cumsum.png" if prefix else None)
        visualizer.plot_ic_distribution(ic_series, title=f"{col} IC分布",
                                         save_path=f"{prefix}_dist.png" if prefix else None)
        
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        ic_ir = ic_mean / ic_std if ic_std != 0 else 0
        
        results[col] = {
            "ic_mean": ic_mean,
            "ic_std": ic_std,
            "ic_ir": ic_ir,
            "ic_positive_rate": (ic_series > 0).mean(),
        }
        
        print(f"{col}: IC={ic_mean:.4f}, IR={ic_ir:.4f}, 正收益占比={results[col]['ic_positive_rate']:.2%}")
    
    return results