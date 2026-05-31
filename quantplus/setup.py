from setuptools import setup, find_packages

setup(
    name="quantplus",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "akshare",
        "baostock",
        "tushare",
        "plotly",
        "backtrader",
        "scikit-learn",
        "joblib",
        "scipy",
    ],
    python_requires=">=3.8",
)