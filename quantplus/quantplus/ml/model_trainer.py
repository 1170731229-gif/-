import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report

class ModelTrainer:
    def __init__(self, model_type: str = "rf"):
        self.model_type = model_type
        self.model = None

    def build_model(self):
        if self.model_type == "rf":
            self.model = RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=42
            )
        elif self.model_type == "gb":
            self.model = GradientBoostingClassifier(
                n_estimators=100, max_depth=5, random_state=42
            )
        elif self.model_type == "lr":
            self.model = LogisticRegression(random_state=42)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        if self.model is None:
            self.build_model()
        self.model.fit(X_train, y_train)

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise ValueError("模型未训练，请先调用 train()")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise ValueError("模型未训练，请先调用 train()")
        return self.model.predict_proba(X)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        y_pred = self.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        return {
            "accuracy": accuracy,
            "report": report
        }

    def cross_validate(self, X: np.ndarray, y: np.ndarray, n_splits: int = 5):
        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            self.train(X_train, y_train)
            scores.append(self.evaluate(X_test, y_test)["accuracy"])
        return {"cv_scores": scores, "mean": np.mean(scores), "std": np.std(scores)}