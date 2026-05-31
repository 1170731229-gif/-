"""
因子正交化模块 - 市值中性化、行业中性化、正交基构建
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.decomposition import PCA


class FactorNeutralizer:
    def __init__(self, method: str = "regression"):
        self.method = method
    
    def neutralize(
        self,
        factor_df: pd.DataFrame,
        factor_col: str,
        neutralize_cols: List[str],
        method: str = "regression"
    ) -> pd.Series:
        """对因子进行中性化处理"""
        if method == "regression":
            return self._regression_neutralize(factor_df, factor_col, neutralize_cols)
        elif method == "rank":
            return self._rank_neutralize(factor_df, factor_col, neutralize_cols)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _regression_neutralize(
        self,
        factor_df: pd.DataFrame,
        factor_col: str,
        neutralize_cols: List[str]
    ) -> pd.Series:
        """回归中性化"""
        available_cols = [c for c in neutralize_cols if c in factor_df.columns]
        
        if not available_cols:
            return factor_df[factor_col]
        
        X = factor_df[available_cols].fillna(0).values
        y = factor_df[factor_col].fillna(0).values
        
        model = LinearRegression()
        model.fit(X, y)
        
        residuals = y - model.predict(X)
        
        return pd.Series(residuals, index=factor_df.index)
    
    def _rank_neutralize(
        self,
        factor_df: pd.DataFrame,
        factor_col: str,
        neutralize_cols: List[str]
    ) -> pd.Series:
        """横截面排序中性化"""
        available_cols = [c for c in neutralize_cols if c in factor_df.columns]
        
        if not available_cols:
            return factor_df[factor_col]
        
        neutralized = factor_df[factor_col].copy()
        
        for col in available_cols:
            neutralized = neutralized - factor_df.groupby(col)[factor_col].transform("median")
        
        return neutralized
    
    def neutralize_group(
        self,
        factor_df: pd.DataFrame,
        factor_col: str,
        group_col: str
    ) -> pd.Series:
        """行业内中性化"""
        return factor_df.groupby(group_col)[factor_col].transform(
            lambda x: x - x.mean()
        )
    
    def neutralize_winsorize(
        self,
        factor_df: pd.DataFrame,
        factor_col: str,
        lower: float = 0.01,
        upper: float = 0.99
    ) -> pd.Series:
        """去极值处理"""
        series = factor_df[factor_col].copy()
        
        lower_val = series.quantile(lower)
        upper_val = series.quantile(upper)
        
        series = series.clip(lower=lower_val, upper=upper_val)
        
        return series
    
    def neutralize_standardize(
        self,
        factor_df: pd.DataFrame,
        factor_col: str
    ) -> pd.Series:
        """标准化处理"""
        series = factor_df[factor_col].copy()
        return (series - series.mean()) / series.std()
    
    def full_neutralize(
        self,
        factor_df: pd.DataFrame,
        factor_col: str,
        neutralize_cols: Optional[List[str]] = None,
        group_col: Optional[str] = None,
        winsorize: bool = True,
        standardize: bool = True
    ) -> pd.Series:
        """完整中性化流程"""
        result = factor_df[factor_col].copy()
        
        if winsorize:
            result = self.neutralize_winsorize(factor_df, factor_col)
        
        if neutralize_cols:
            result = self.neutralize(result.to_frame(), factor_col, neutralize_cols)
        
        if group_col and group_col in factor_df.columns:
            temp_df = factor_df.copy()
            temp_df["_temp_factor"] = result
            result = self.neutralize_group(temp_df, "_temp_factor", group_col)
        
        if standardize:
            result = (result - result.mean()) / result.std()
        
        return result


class FactorOrthogonalizer:
    """因子正交基构建"""
    
    @staticmethod
    def gram_schmidt(
        factors: pd.DataFrame,
        normalize: bool = True
    ) -> pd.DataFrame:
        """Gram-Schmidt正交化"""
        factors = factors.fillna(0)
        ortho_factors = pd.DataFrame(index=factors.index)
        
        prev_factor = None
        for i, col in enumerate(factors.columns):
            if i == 0:
                ortho = factors[col].copy()
            else:
                ortho = factors[col].copy()
                for prev_col in ortho_factors.columns:
                    projection = (factors[col] * ortho_factors[prev_col]).sum()
                    if normalize:
                        norm_sq = (ortho_factors[prev_col] ** 2).sum()
                        if norm_sq > 0:
                            projection = projection / norm_sq * ortho_factors[prev_col]
                    ortho = ortho - projection
            
            if normalize and ortho.std() > 0:
                ortho = (ortho - ortho.mean()) / ortho.std()
            
            ortho_factors[f"ortho_{i}"] = ortho
        
        return ortho_factors
    
    @staticmethod
    def pca_orthogonalize(
        factors: pd.DataFrame,
        n_components: Optional[int] = None,
        explained_var_threshold: float = 0.95
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """PCA正交化降维"""
        factors = factors.fillna(0)
        
        if n_components is None:
            pca = PCA()
            pca.fit(factors)
            cumsum = np.cumsum(pca.explained_variance_ratio_)
            n_components = np.argmax(cumsum >= explained_var_threshold) + 1
        
        pca = PCA(n_components=n_components)
        components = pca.fit_transform(factors)
        
        components_df = pd.DataFrame(
            components,
            index=factors.index,
            columns=[f"PC{i+1}" for i in range(n_components)]
        )
        
        explained_df = pd.DataFrame({
            "explained_variance": pca.explained_variance_,
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "cumulative_variance_ratio": np.cumsum(pca.explained_variance_ratio_)
        })
        
        return components_df, explained_df
    
    @staticmethod
    def residualize(
        target: pd.Series,
        factors: pd.DataFrame,
        method: str = "ridge",
        alpha: float = 1.0
    ) -> pd.Series:
        """残差化（对目标因子对其他因子回归取残差）"""
        X = factors.fillna(0).values
        y = target.fillna(0).values
        
        if method == "ridge":
            model = Ridge(alpha=alpha)
        else:
            model = LinearRegression()
        
        model.fit(X, y)
        residuals = y - model.predict(X)
        
        return pd.Series(residuals, index=target.index)


class MultiFactorNeutralization:
    """多因子中性化流水线"""
    
    def __init__(self):
        self.neutralizer = FactorNeutralizer()
        self.orthogonalizer = FactorOrthogonalizer()
        self.processed_factors = {}
    
    def process(
        self,
        factor_df: pd.DataFrame,
        factor_cols: List[str],
        neutralize_cols: Optional[List[str]] = None,
        group_col: Optional[str] = None,
        orthogonalize: bool = False,
        orthogonalize_method: str = "pca"
    ) -> pd.DataFrame:
        """完整处理流水线"""
        result = factor_df.copy()
        
        for col in factor_cols:
            neutralized = self.neutralizer.full_neutralize(
                result,
                col,
                neutralize_cols=neutralize_cols,
                group_col=group_col
            )
            result[f"{col}_neutralized"] = neutralized
            self.processed_factors[col] = f"{col}_neutralized"
        
        if orthogonalize:
            ortho_cols = [self.processed_factors[c] for c in factor_cols 
                         if c in self.processed_factors]
            
            if orthogonalize_method == "pca":
                components, explained = self.orthogonalizer.pca_orthogonalize(
                    result[ortho_cols]
                )
                for col in components.columns:
                    result[col] = components[col]
            else:
                ortho = self.orthogonalizer.gram_schmidt(result[ortho_cols])
                for col in ortho.columns:
                    result[col] = ortho[col]
        
        return result
    
    def batch_neutralize(
        self,
        factor_df: pd.DataFrame,
        factor_cols: List[str],
        neutralize_cols: List[str]
    ) -> pd.DataFrame:
        """批量中性化"""
        result = pd.DataFrame(index=factor_df.index)
        
        for col in factor_cols:
            result[f"{col}_neutral"] = self.neutralizer.neutralize(
                factor_df, col, neutralize_cols
            )
        
        return result