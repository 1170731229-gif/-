"""
机器学习因子策略使用示例
"""

from quantplus.factor import (
    FactorBuilder, FactorEvaluator, 
    create_ml_strategy, run_ml_backtest
)
from quantplus.data.fetcher import AkshareSource
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression


def example_factor_building():
    """示例1: 构建因子数据集"""
    fetcher = AkshareSource()
    df = fetcher.get_daily("600519", "20230101", "20240101")
    
    builder = (
        FactorBuilder()
        .add_return_factor(periods=[1, 5, 10])
        .add_ma_factor(periods=[5, 20, 60])
        .add_volatility_factor(periods=[5, 20])
        .add_rsi_factor(periods=[6, 12])
        .add_momentum_factor(periods=[5, 10])
    )
    
    factor_df = builder.build(df, forward=5, label_type="binary", threshold=0.02)
    
    print(f"特征数量: {len(builder.factors)}")
    print(f"样本数量: {len(factor_df)}")
    print(f"特征列: {[c for c in factor_df.columns if c not in ['date', 'open', 'high', 'low', 'close', 'volume', 'label']]}")
    
    return factor_df


def example_factor_evaluation():
    """示例2: 因子评估"""
    factor_df = example_factor_building()
    
    for factor_col in ["return_5", "ma_ratio_5_20", "rsi_12", "momentum_10"]:
        if factor_col not in factor_df.columns:
            continue
        
        report = FactorEvaluator.full_evaluation(factor_df, factor_col)
        print(f"\n=== {factor_col} ===")
        print(f"IC均值: {report['ic_mean']:.4f}")
        print(f"IC IR: {report['ic_ir']:.4f}")
        print(f"IC正收益占比: {report['ic_positive_rate']:.2%}")


def example_ml_strategy():
    """示例3: ML策略回测"""
    fetcher = AkshareSource()
    df = fetcher.get_daily("600519", "20230101", "20240601")
    
    results = run_ml_backtest(
        df,
        model=GradientBoostingClassifier(n_estimators=50, max_depth=3),
        initial_cash=100000,
        lookback=20
    )
    
    return results


def example_custom_model():
    """示例4: 使用自定义模型"""
    fetcher = AkshareSource()
    df = fetcher.get_daily("600519", "20230101", "20240601")
    
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    
    StrategyClass = create_ml_strategy(
        model=model,
        lookback=30,
        predict_threshold=0.55
    )
    
    from backtrader import Cerebro
    import backtrader as bt
    
    cerebro = Cerebro()
    cerebro.addstrategy(StrategyClass)
    
    data = bt.feeds.PandasData(dataname=df.set_index("date"))
    cerebro.adddata(data)
    cerebro.broker.setcash(100000)
    
    print(f"初始资金: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"最终资金: {cerebro.broker.getvalue():.2f}")


def example_generate_factor():
    """示例5: 生成因子信号序列"""
    fetcher = AkshareSource()
    df = fetcher.get_daily("600519", "20230101", "20240101")
    
    builder = (
        FactorBuilder()
        .add_return_factor()
        .add_ma_ratio_factor()
    )
    
    factor_df = builder.build(df, forward=5)
    
    factor_df["predict_probability"] = 0.5
    
    df_with_factor = df.merge(
        factor_df[["date", "return_5", "ma_ratio_5_20", "label"]],
        on="date",
        how="left"
    )
    
    print(df_with_factor[["date", "close", "return_5", "ma_ratio_5_20", "predict_probability"]].tail(10))


if __name__ == "__main__":
    print("=" * 50)
    print("示例1: 构建因子数据集")
    print("=" * 50)
    example_factor_building()
    
    print("\n" + "=" * 50)
    print("示例2: 因子评估")
    print("=" * 50)
    example_factor_evaluation()


def example_ic_visualization():
    """示例6: IC分析可视化"""
    from quantplus.factor import FactorBuilder, FactorEvaluator, FactorVisualizer
    
    fetcher = AkshareSource()
    df = fetcher.get_daily("600519", "20230101", "20240601")
    
    builder = (
        FactorBuilder()
        .add_return_factor(periods=[1, 5, 10])
        .add_ma_ratio_factor(periods=[(5, 20), (10, 60)])
        .add_volatility_factor(periods=[5, 20])
        .add_rsi_factor(periods=[6, 12])
    )
    
    factor_df = builder.build(df, forward=5, label_type="binary")
    
    viz = FactorVisualizer()
    
    ic_results = {}
    for col in ["return_5", "return_10", "ma_ratio_5_20", "rsi_12"]:
        if col not in factor_df.columns:
            continue
        
        ic_series = FactorEvaluator.calculate_ic(factor_df, col)
        ic_results[col] = ic_series
        
        viz.plot_ic_series(ic_series, title=f"{col} IC序列")
        viz.plot_ic_cumulative(ic_series, title=f"{col} IC累积曲线")
        viz.plot_ic_distribution(ic_series, title=f"{col} IC分布")
    
    print("IC分析图表已生成")
    return ic_results


def example_factor_neutralization():
    """示例7: 因子正交化"""
    from quantplus.factor import (
        FactorBuilder, FactorNeutralizer, FactorOrthogonalizer
    )
    
    fetcher = AkshareSource()
    df = fetcher.get_daily("600519", "20230101", "20240601")
    
    builder = (
        FactorBuilder()
        .add_return_factor(periods=[1, 5, 10])
        .add_volatility_factor(periods=[5, 20])
        .add_momentum_factor(periods=[5, 10])
    )
    
    factor_df = builder.build(df, forward=5, label_type="binary")
    
    neutralizer = FactorNeutralizer()
    
    neutralize_cols = ["return_1", "volatility_5"]
    for col in ["return_5", "momentum_5"]:
        if col not in factor_df.columns:
            continue
        
        factor_df[f"{col}_neutral"] = neutralizer.neutralize(
            factor_df, col, neutralize_cols
        )
        
        print(f"\n{col} 中性化前后对比:")
        print(f"  原始IC: {factor_df[col].corr(factor_df['label'], method='spearman'):.4f}")
        print(f"  中性化IC: {factor_df[f'{col}_neutral'].corr(factor_df['label'], method='spearman'):.4f}")
    
    orthogonalizer = FactorOrthogonalizer()
    
    factor_cols = ["return_5", "return_10", "momentum_5", "momentum_10"]
    available_cols = [c for c in factor_cols if c in factor_df.columns]
    
    if available_cols:
        ortho_df = orthogonalizer.gram_schmidt(factor_df[available_cols])
        factor_df = pd.concat([factor_df, ortho_df], axis=1)
        
        print("\nGram-Schmidt正交化结果相关性:")
        print(ortho_df.corr())
    
    return factor_df


def example_multi_factor_pipeline():
    """示例8: 多因子处理流水线"""
    from quantplus.factor import (
        FactorBuilder, MultiFactorNeutralization, FactorEvaluator, FactorVisualizer
    )
    
    fetcher = AkshareSource()
    df = fetcher.get_daily("600519", "20230101", "20240601")
    
    builder = (
        FactorBuilder()
        .add_return_factor(periods=[1, 5, 10])
        .add_ma_factor(periods=[5, 20, 60])
        .add_volatility_factor(periods=[5, 20])
        .add_rsi_factor(periods=[6, 12])
        .add_momentum_factor(periods=[5, 10])
    )
    
    factor_df = builder.build(df, forward=5, label_type="binary")
    
    pipeline = MultiFactorNeutralization()
    
    factor_cols = ["return_5", "return_10", "rsi_12", "momentum_10"]
    neutralize_cols = ["return_1", "volatility_5", "ma_5"]
    
    result_df = pipeline.process(
        factor_df,
        factor_cols=factor_cols,
        neutralize_cols=neutralize_cols,
        orthogonalize=True,
        orthogonalize_method="pca"
    )
    
    print("多因子中性化结果:")
    for col in factor_cols:
        neutral_col = f"{col}_neutralized"
        if neutral_col in result_df.columns:
            original_ic = FactorEvaluator.calculate_ic(factor_df, col).mean()
            neutral_ic = FactorEvaluator.calculate_ic(result_df, neutral_col).mean()
            print(f"  {col}: {original_ic:.4f} -> {neutral_ic:.4f}")


if __name__ == "__main__" and False:
    print("=" * 50)
    print("示例6: IC分析可视化")
    print("=" * 50)
    example_ic_visualization()
    
    print("\n" + "=" * 50)
    print("示例7: 因子正交化")
    print("=" * 50)
    example_factor_neutralization()
    
    print("\n" + "=" * 50)
    print("示例8: 多因子处理流水线")
    print("=" * 50)
    example_multi_factor_pipeline()