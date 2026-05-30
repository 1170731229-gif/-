import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

class MLFeatureBuilder:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []

    def build_features(self, df: pd.DataFrame, target_col: str = "return_1d") -> tuple:
        """
        构建机器学习特征
        返回: (X, y, feature_names)
        """
        result = df.copy()
        result["return_1d"] = result["close"].pct_change()
        result["return_5d"] = result["close"].pct_change(5)
        result["return_10d"] = result["close"].pct_change(10)
        result["volatility_5d"] = result["return_1d"].rolling(5).std()
        result["volatility_20d"] = result["return_1d"].rolling(20).std()
        result["ma5"] = result["close"].rolling(5).mean()
        result["ma20"] = result["close"].rolling(20).mean()
        result["ma_ratio"] = result["ma5"] / result["ma20"]
        result["volume_ratio"] = result["volume"] / result["volume"].rolling(20).mean()
        result["high_low_ratio"] = (result["high"] - result["low"]) / result["close"]
        result["upper_shadow"] = (result["high"] - result[["open", "close"]].max(axis=1)) / result["close"]
        result["lower_shadow"] = (result[["open", "close"]].min(axis=1) - result["low"]) / result["close"]

        feature_cols = [
            "return_1d", "return_5d", "return_10d",
            "volatility_5d", "volatility_20d", "ma_ratio",
            "volume_ratio", "high_low_ratio", "upper_shadow", "lower_shadow"
        ]

        self.feature_names = feature_cols
        result = result.dropna()
        X = result[feature_cols].values
        y = (result[target_col] > 0).astype(int).values

        return X, y, feature_cols

    def scale_features(self, X_train: np.ndarray, X_test: np.ndarray = None):
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
            return X_train_scaled, X_test_scaled
        return X_train_scaled