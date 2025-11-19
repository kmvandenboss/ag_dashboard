#!/usr/bin/env python3
"""
Feature Engineering for Corn Futures Predictive Models
Phase 1: Create derived features for Model 1-4

This script:
1. Loads the base combined dataset (77 columns)
2. Creates forward return targets (NO DATA LEAKAGE)
3. Engineers trailing returns, volatility, volume, seasonal, technical, weather, and sentiment features
4. Creates lag features
5. Validates no data leakage
6. Saves enhanced dataset with 120+ features
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# File paths
INPUT_FILE = "data/corn_combined.csv"
OUTPUT_FILE = "data/corn_combined_features.csv"

print("="*60)
print("PHASE 1: FEATURE ENGINEERING")
print("="*60)

# ============================================================================
# LOAD DATA
# ============================================================================
print("\n[1/10] Loading base dataset...")
df = pd.read_csv(INPUT_FILE, parse_dates=['date'])
print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

# Sort by date to ensure proper ordering
df = df.sort_values('date').reset_index(drop=True)

# ============================================================================
# FORWARD RETURN TARGETS (SAFE - These are targets, not features)
# ============================================================================
print("\n[2/10] Creating forward return targets...")

def add_forward_returns(df, horizons=(1, 3, 5, 10, 20)):
    """
    For each horizon h, create fwd_ret_{h}d = (close[t+h] / close[t] - 1).

    At row t:
    - All features use data ≤ t (safe)
    - Target uses close[t] and close[t+h] (forward-looking, that's the point)
    - Drop last h rows where target is NaN when training

    Parameters:
        df: DataFrame with 'close' column
        horizons: tuple of forecast horizons in days

    Returns:
        df with new columns: fwd_ret_1d, fwd_ret_3d, fwd_ret_5d, etc.
    """
    for h in horizons:
        df[f"fwd_ret_{h}d"] = df["close"].shift(-h) / df["close"] - 1.0
        print(f"  Created fwd_ret_{h}d (target)")
    return df

df = add_forward_returns(df, horizons=(1, 3, 5, 10, 20))

# Binary targets for classification (Model 1)
print("\n  Creating binary targets for classification...")
for h in [1, 3, 5, 10, 20]:
    df[f'target_up_{h}d'] = (df[f'fwd_ret_{h}d'] > 0).astype(int)
    print(f"  Created target_up_{h}d (1 if return > 0, else 0)")

# ============================================================================
# TRAILING RETURNS (SAFE - Backward-looking features)
# ============================================================================
print("\n[3/10] Engineering trailing return features...")

# Note: ret_1d already exists in base dataset, but we'll recreate for consistency
df['ret_1d'] = df['close'] / df['close'].shift(1) - 1
df['ret_3d_trailing'] = df['close'] / df['close'].shift(3) - 1
df['ret_5d_trailing'] = df['close'] / df['close'].shift(5) - 1
df['ret_10d_trailing'] = df['close'] / df['close'].shift(10) - 1
df['ret_20d_trailing'] = df['close'] / df['close'].shift(20) - 1
df['ret_60d_trailing'] = df['close'] / df['close'].shift(60) - 1

print(f"  Created 6 trailing return features")

# ============================================================================
# VOLATILITY FEATURES (SAFE - Rolling windows look backward)
# ============================================================================
print("\n[4/10] Engineering volatility and volume features...")

# Realized volatility (annualized)
df['vol_5d'] = df['ret_1d'].rolling(5).std() * (252**0.5)
df['vol_10d'] = df['ret_1d'].rolling(10).std() * (252**0.5)
df['vol_20d'] = df['ret_1d'].rolling(20).std() * (252**0.5)
df['vol_60d'] = df['ret_1d'].rolling(60).std() * (252**0.5)

# Volatility z-score (for regime detection)
df['vol_zscore_20d'] = (df['vol_20d'] - df['vol_20d'].rolling(252).mean()) / df['vol_20d'].rolling(252).std()
df['vol_zscore_60d'] = (df['vol_60d'] - df['vol_60d'].rolling(252).mean()) / df['vol_60d'].rolling(252).std()

# Volume features
df['volume_20d_avg'] = df['volume'].rolling(20).mean()
df['volume_60d_avg'] = df['volume'].rolling(60).mean()

# Volume ratio (current vs average)
df['volume_ratio_20d'] = df['volume'] / df['volume_20d_avg']
df['volume_ratio_60d'] = df['volume'] / df['volume_60d_avg']

# Volume z-score
df['volume_zscore_20d'] = (df['volume'] - df['volume_20d_avg']) / df['volume'].rolling(20).std()

print(f"  Created 11 volatility/volume features")

# ============================================================================
# SEASONAL FEATURES (SAFE - Calendar-based)
# ============================================================================
print("\n[5/10] Engineering seasonal features...")

# Calendar features
df['month'] = df['date'].dt.month
df['day_of_year'] = df['date'].dt.dayofyear
df['week_of_year'] = df['date'].dt.isocalendar().week
df['quarter'] = df['date'].dt.quarter

# Corn growing season indicators
df['is_planting_season'] = df['month'].isin([4, 5, 6]).astype(int)      # Apr-Jun
df['is_pollination_season'] = df['month'].isin([6, 7]).astype(int)      # Jun-Jul (critical)
df['is_harvest_season'] = df['month'].isin([9, 10, 11]).astype(int)     # Sep-Nov

# Seasonal dummies (for tree models, month is sufficient; these are for reference)
for m in range(1, 13):
    df[f'month_{m}'] = (df['month'] == m).astype(int)

print(f"  Created 20 seasonal features")

# ============================================================================
# MOMENTUM/TECHNICAL INDICATORS (SAFE - Backward-looking)
# ============================================================================
print("\n[6/10] Engineering momentum/technical indicators...")

# Moving averages
df['ma_20'] = df['close'].rolling(20).mean()
df['ma_50'] = df['close'].rolling(50).mean()
df['ma_200'] = df['close'].rolling(200).mean()

# Price relative to MA
df['close_vs_ma20'] = (df['close'] / df['ma_20']) - 1
df['close_vs_ma50'] = (df['close'] / df['ma_50']) - 1
df['close_vs_ma200'] = (df['close'] / df['ma_200']) - 1

# RSI (14-day)
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['rsi_14'] = calculate_rsi(df['close'], period=14)
df['rsi_28'] = calculate_rsi(df['close'], period=28)

# Bollinger Bands
df['bb_upper'] = df['ma_20'] + (df['close'].rolling(20).std() * 2)
df['bb_lower'] = df['ma_20'] - (df['close'].rolling(20).std() * 2)
df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['ma_20']
df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

# Price momentum (rate of change)
df['roc_5d'] = df['close'] / df['close'].shift(5) - 1
df['roc_20d'] = df['close'] / df['close'].shift(20) - 1

print(f"  Created 15 momentum/technical features")

# ============================================================================
# WEATHER COMPOSITE INDICATORS (SAFE - Based on current/past weather)
# ============================================================================
print("\n[7/10] Engineering weather composite indicators...")

# Drought indicator
df['drought_indicator'] = ((df['prcp_30d'] < 2.0) & (df['heat_stress'] > 5)).astype(int)

# Extreme heat indicator
df['extreme_heat'] = (df['tmax'] > 95).astype(int)

# Consecutive dry days (rolling count)
df['dry_days_7d'] = df['dry_day'].rolling(7).sum()
df['dry_days_14d'] = df['dry_day'].rolling(14).sum()
df['dry_days_30d'] = df['dry_day'].rolling(30).sum()

# Growing stress index (during critical months Jun-Jul)
df['growing_stress'] = 0.0
critical_months = df['month'].isin([6, 7])  # June-July pollination

# Only calculate stress during critical months
if df['heat_stress'].notna().any() and df['prcp_30d'].notna().any():
    df.loc[critical_months, 'growing_stress'] = (
        (df.loc[critical_months, 'heat_stress'].fillna(0) * 0.5) +
        ((10 - df.loc[critical_months, 'prcp_30d'].fillna(5).clip(0, 10)) * 0.5)
    )

# GDD rolling sums
df['gdd_7d'] = df['gdd'].rolling(7).sum()
df['gdd_14d'] = df['gdd'].rolling(14).sum()
df['gdd_30d'] = df['gdd'].rolling(30).sum()

# Temperature extremes
df['temp_range'] = df['tmax'] - df['tmin']
df['temp_range_7d_avg'] = df['temp_range'].rolling(7).mean()

print(f"  Created 12 weather composite features")

# ============================================================================
# SENTIMENT COMPOSITE INDICATORS (SAFE - Based on current COT/options data)
# ============================================================================
print("\n[8/10] Engineering sentiment composite indicators...")

# Combined speculator positioning (COT futures + options)
df['speculator_net_combined'] = df['mm_net'].fillna(0) + df['mm_net_position'].fillna(0)

# Sentiment extremes
df['sentiment_extreme'] = (
    (df['put_call_ratio_52w_pct'] > 80) |  # Extreme fear
    (df['put_call_ratio_52w_pct'] < 20) |  # Extreme greed
    (df['mm_net_index'] > 90) |             # MM very long
    (df['mm_net_index'] < 10)               # MM very short
).astype(int)

# COT changes (week-over-week)
df['mm_net_change_1w'] = df['mm_net'].diff(7)  # Weekly COT data
df['mm_net_change_4w'] = df['mm_net'].diff(28)

# Options sentiment
df['dealer_mm_net_diff'] = df['dealer_net_position'].fillna(0) - df['mm_net_position'].fillna(0)

# COT positioning z-scores
df['mm_net_zscore'] = (df['mm_net'] - df['mm_net'].rolling(252).mean()) / df['mm_net'].rolling(252).std()
df['prod_net_zscore'] = (df['prod_net'] - df['prod_net'].rolling(252).mean()) / df['prod_net'].rolling(252).std()

print(f"  Created 7 sentiment composite features")

# ============================================================================
# FUNDAMENTAL RATIOS (SAFE - Based on current WASDE data)
# ============================================================================
print("\n  Engineering fundamental ratios...")

# Stocks-to-use ratio approximation (lower = tighter supply = bullish)
# Note: This is a rough approximation; true stocks-to-use needs total usage
df['stocks_to_exports_ratio'] = df['ending_stocks_mbu'] / (df['exports_mbu'] + 1)  # +1 to avoid division by zero

# WASDE changes (month-over-month approximations)
df['yield_change_1m'] = df['yield_estimate_bu_per_acre'].diff(21)  # ~1 month
df['yield_change_3m'] = df['yield_estimate_bu_per_acre'].diff(63)  # ~3 months
df['stocks_change_1m'] = df['ending_stocks_mbu'].diff(21)
df['stocks_change_3m'] = df['ending_stocks_mbu'].diff(63)

# Production change
df['production_change_1m'] = df['production_mbu'].diff(21)

# Crop condition changes
df['condition_index_change_1w'] = df['condition_index'].diff(7)
df['condition_index_change_4w'] = df['condition_index'].diff(28)

print(f"  Created 8 fundamental ratio features")

# ============================================================================
# LAG FEATURES (SAFE - Explicitly using past data)
# ============================================================================
print("\n[9/10] Creating lag features for key variables...")

lag_features_config = {
    'condition_index': [1, 7, 14],      # Crop conditions impact with delay
    'mm_net': [7, 14],                  # COT positioning weekly
    'prcp_30d': [1, 7],                 # Rainfall effects
    'heat_stress': [1, 7],              # Heat stress delayed impact
    'put_call_ratio_52w_pct': [7, 14],  # Sentiment shifts
    'vol_20d': [1, 5, 10],              # Volatility persistence
    'close': [1, 3, 5, 10, 20]          # Price lags
}

lag_count = 0
for feature, lags in lag_features_config.items():
    if feature in df.columns:
        for lag in lags:
            new_col = f'{feature}_lag{lag}'
            df[new_col] = df[feature].shift(lag)
            lag_count += 1

print(f"  Created {lag_count} lag features")

# ============================================================================
# DATA VALIDATION - CHECK FOR LEAKAGE
# ============================================================================
print("\n[10/10] Validating no data leakage...")

# List all columns
all_columns = df.columns.tolist()

# Identify target columns (should NOT be used as features)
target_cols = [col for col in all_columns if col.startswith('fwd_ret_') or col.startswith('target_up_')]

# Identify feature columns (everything except date, targets, and redundant columns)
exclude_cols = target_cols + ['date', 'adj_close', 'notes']
feature_cols = [col for col in all_columns if col not in exclude_cols]

print(f"\n  Total columns: {len(all_columns)}")
print(f"  Target columns: {len(target_cols)}")
print(f"  Feature columns: {len(feature_cols)}")
print(f"  Excluded columns: {len(exclude_cols)}")

# Check for any suspicious columns that might leak future data
suspicious = []
for col in feature_cols:
    if 'fwd' in col.lower() and 'ret' in col.lower():
        suspicious.append(col)
    if 'future' in col.lower():
        suspicious.append(col)
    if 'next' in col.lower():
        suspicious.append(col)

if suspicious:
    print(f"\n  ⚠️  WARNING: Potentially leaky features detected:")
    for col in suspicious:
        print(f"    - {col}")
else:
    print(f"\n  [OK] No data leakage detected")

# ============================================================================
# SAVE ENHANCED DATASET
# ============================================================================
print(f"\n{'='*60}")
print("SAVING ENHANCED DATASET")
print(f"{'='*60}")

df.to_csv(OUTPUT_FILE, index=False)
print(f"\n  Saved to: {OUTPUT_FILE}")
print(f"  Total rows: {len(df)}")
print(f"  Total columns: {len(df.columns)}")
print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print(f"\n{'='*60}")
print("FEATURE SUMMARY")
print(f"{'='*60}")

feature_groups = {
    'Forward Returns (Targets)': [col for col in all_columns if col.startswith('fwd_ret_')],
    'Binary Targets': [col for col in all_columns if col.startswith('target_up_')],
    'Trailing Returns': [col for col in feature_cols if 'ret_' in col and 'trailing' in col] + ['ret_1d', 'ret_3d_trailing', 'ret_5d_trailing'],
    'Volatility': [col for col in feature_cols if 'vol_' in col],
    'Volume': [col for col in feature_cols if 'volume' in col],
    'Seasonal': [col for col in feature_cols if col in ['month', 'day_of_year', 'week_of_year', 'quarter', 'is_planting_season', 'is_pollination_season', 'is_harvest_season'] or col.startswith('month_')],
    'Technical/Momentum': [col for col in feature_cols if any(x in col for x in ['ma_', 'rsi_', 'bb_', 'roc_', 'close_vs'])],
    'Weather Composites': [col for col in feature_cols if any(x in col for x in ['drought', 'extreme_heat', 'dry_days', 'growing_stress', 'gdd_', 'temp_range'])],
    'Sentiment Composites': [col for col in feature_cols if any(x in col for x in ['speculator', 'sentiment_extreme', 'mm_net_change', 'dealer_mm', '_zscore']) and 'vol' not in col],
    'Fundamental Ratios': [col for col in feature_cols if any(x in col for x in ['stocks_to', 'yield_change', 'stocks_change', 'production_change', 'condition_index_change'])],
    'Lag Features': [col for col in feature_cols if '_lag' in col]
}

print("\nFeatures by Category:")
for group, cols in feature_groups.items():
    print(f"  {group}: {len(cols)}")

# Missing data summary
print(f"\n{'='*60}")
print("MISSING DATA SUMMARY")
print(f"{'='*60}")

missing_summary = df[feature_cols].isnull().sum().sort_values(ascending=False)
top_missing = missing_summary.head(15)

print(f"\nTop 15 features with missing data:")
for col, count in top_missing.items():
    pct = (count / len(df)) * 100
    print(f"  {col}: {count} ({pct:.1f}%)")

# Data types
print(f"\n{'='*60}")
print("DATA TYPES")
print(f"{'='*60}")

print("\nData type distribution:")
print(df[feature_cols].dtypes.value_counts())

print(f"\n{'='*60}")
print("[SUCCESS] PHASE 1 COMPLETE")
print(f"{'='*60}")
print(f"\nNext steps:")
print(f"  1. Review features in: {OUTPUT_FILE}")
print(f"  2. Run Phase 2: Model 1 - Feature Importance")
print(f"  3. Check for any unexpected patterns or issues")
