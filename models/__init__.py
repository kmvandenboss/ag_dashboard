"""
Production Models Module

Contains trained XGBoost models for generating trading signals:
- Corn Moderate: Balanced risk/reward (20% R per trade)
- Corn Growth: Aggressive growth-oriented (30% R per trade)
- Corn High Conviction: Selective high-confidence signals (90th/10th percentile)
- Soybean Moderate: Balanced soybean strategy
- Soybean High Conviction: High-confidence soybean signals
- Conservative v2.0: Low-risk defensive strategy
"""

__version__ = "1.0.0"
