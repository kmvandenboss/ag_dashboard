# Moderate Soybean Model - Documentation

**Model Type**: Moderate Risk (20% R per trade)
**Commodity**: Soybean Futures (ZS=F)
**Version**: 1.0
**Created**: 2025-11-16
**Status**: Ready for Training (pending data collection)

---

## Table of Contents

1. [Overview](#overview)
2. [Model Architecture](#model-architecture)
3. [Configuration](#configuration)
4. [Expected Performance](#expected-performance)
5. [Setup Instructions](#setup-instructions)
6. [Validation Methodology](#validation-methodology)
7. [Comparison to Corn Model](#comparison-to-corn-model)
8. [Usage](#usage)

---

## Overview

The Moderate Soybean Model is a machine learning-based trading system designed for soybean futures. It fills the gap between conservative and aggressive strategies, targeting **30-35% annual returns** with **-8% to -10% average drawdown**.

### Key Characteristics

- **Position Sizing**: 20% R (Risk) per trade
- **Entry Strategy**: Trade top 15% and bottom 15% of predictions (85th/15th percentile)
- **Stop Loss**: 3.5× ATR (Average True Range)
- **Profit Target**: 2.0R (lock in wins at 2× risk amount)
- **Time Stop**: 10 days maximum hold period
- **Max Concurrent**: 5 positions
- **Prediction Horizon**: 10-day forward returns

### Risk Profile

| Metric | Target |
|--------|--------|
| **Annual Return** | 30-35% |
| **Sharpe Ratio** | 2.5 |
| **Max Drawdown** | -8% |
| **Win Rate** | 70% |
| **Trades/Year** | ~86 |

---

## Model Architecture

### Machine Learning Model

**Type**: XGBoost Regressor (Gradient Boosted Trees)

**Hyperparameters**:
- `n_estimators`: 300 trees
- `max_depth`: 6 levels
- `learning_rate`: 0.03
- `subsample`: 0.8
- `colsample_bytree`: 0.8
- `random_state`: 42 (reproducibility)

**Target**: `fwd_ret_10d` (10-day forward return)

### Feature Set

**Total Features**: 179

**Feature Categories**:

1. **Price Data** (8 features)
   - OHLC, volume, adjusted close, open interest

2. **Technical Indicators** (40+ features)
   - Returns: 1d, 5d, 10d, 20d (trailing)
   - Volatility: 20d, 60d rolling
   - Momentum: RSI, MACD, price z-scores
   - Moving averages: 5d, 20d, 50d, 200d

3. **USDA Fundamentals** (15+ features)
   - Yield estimates (bu/acre)
   - Production (million bushels)
   - Ending stocks
   - Exports
   - Stocks-to-use ratio

4. **COT Positioning** (30+ features)
   - Money Manager net positions
   - Producer hedging activity
   - Swap dealer positions
   - Position changes (weekly)
   - Money Manager Index (0-100)

5. **Options Data** (15+ features)
   - Put/call ratios
   - Open interest by trader type
   - Put/call ratio percentiles
   - Options sentiment indicators

6. **Weather** (20+ features)
   - Temperature: max, min, avg
   - Precipitation: daily, 7d, 30d rolling
   - Growing Degree Days (GDD)
   - Heat stress days
   - Dry stress days
   - Soybean Belt weighted index

7. **Crop Conditions** (15+ features)
   - Weekly condition ratings (Excellent, Good, Fair, Poor, Very Poor)
   - Crop progress: Planted, Emerged, Blooming, Pod Setting, Harvest
   - Condition index (0-100 weighted score)

8. **Seasonal/Calendar** (10+ features)
   - Month, quarter, day of year
   - Growing season indicators (May-Nov for soybeans)
   - Critical period flags (Jul-Aug flowering/pod setting)
   - Harvest season flags

9. **Sentiment & Positioning** (20+ features)
   - Net positioning changes
   - Extreme positioning flags
   - Sentiment z-scores
   - Contrarian indicators

### Soybean-Specific Adaptations

Unlike corn, soybeans have different critical periods:

| Period | Corn | Soybeans |
|--------|------|----------|
| **Planting** | Apr-Jun | May-Jun |
| **Critical Growth** | Jun-Jul (pollination/silking) | Jul-Aug (flowering R1-R6, pod setting) |
| **Harvest** | Sep-Nov | Sep-Nov |
| **Top Producer** | Iowa (27.4%) | Illinois (18.0%) |

**Weather Weights** (Soybean Belt):
- Illinois: 18.0% (top producer)
- Iowa: 16.5%
- Minnesota: 11.5%
- Indiana: 10.0%
- Nebraska: 9.5%
- Ohio: 7.0%

---

## Configuration

### Full Configuration (`model_config.json`)

```json
{
  "model_name": "Moderate Soybean (20% R)",
  "version": "1.0",
  "commodity": "soybeans",
  "ticker": "ZS=F",

  "parameters": {
    "position_sizing": {
      "r_per_trade": 0.20,
      "max_concurrent_positions": 5,
      "max_portfolio_risk": 1.0
    },
    "thresholds": {
      "long_percentile": 0.85,
      "short_percentile": 0.15,
      "rolling_window": 100
    },
    "stops": {
      "atr_multiplier": 3.5,
      "atr_period": 20,
      "time_stop_days": 10
    },
    "profit_targets": {
      "enabled": true,
      "target_r": 2.0
    }
  },

  "expected_performance": {
    "avg_annual_return": 0.35,
    "avg_sharpe": 2.5,
    "avg_max_dd": -0.08,
    "avg_win_rate": 0.70,
    "trades_per_year": 86
  }
}
```

### Position Sizing

**20% R per Trade** means:

If you have a $100,000 account:
- Max risk per trade: $20,000 (20% of account)
- If stop loss is 3% away from entry: Position size = $20,000 / 0.03 = $666,667 notional
- With ZS futures ($50/point, 5000 bushels): ~2.6 contracts

**Example Trade**:
- Account: $100,000
- Entry: $12.50
- Stop: $12.00 (3.5× ATR = 50 cents)
- Risk: $0.50 per bushel × 5000 bushels = $2,500 per contract
- Position: $20,000 / $2,500 = 8 contracts
- Profit Target: 2.0R = $40,000 (exit at $13.50)

---

## Expected Performance

### Backtest Projections (Based on Corn Moderate)

The corn Moderate model achieved:
- **74% directional accuracy**
- **3.23 Sharpe ratio**
- **+35% annualized return** (estimate)
- **-10% max drawdown**
- **86 trades/year**

We expect soybeans to perform similarly:

| Metric | Conservative | Expected | Optimistic |
|--------|-------------|----------|------------|
| **Annual Return** | +25% | +35% | +45% |
| **Sharpe Ratio** | 2.0 | 2.5 | 3.0 |
| **Max Drawdown** | -12% | -8% | -6% |
| **Win Rate** | 65% | 70% | 75% |
| **Avg Trade** | +2.5% | +3.1% | +4.0% |
| **Trades/Year** | 70 | 86 | 100 |

### Real-World Adjustments

Subtract from backtest results:
- **Slippage**: -0.5% per trade (2-3 ticks)
- **Commission**: -0.1% per round trip
- **Execution delays**: -0.2% (signal to execution lag)
- **Psychological factors**: -5% annual return (discipline lapses)

**Conservative Real-World Estimate**: +25-30% annual return

---

## Setup Instructions

### Prerequisites

1. **Python Environment**:
   ```bash
   pip install pandas numpy xgboost scikit-learn yfinance requests joblib
   ```

2. **API Keys**:
   - NASS API Key (for crop conditions): https://quickstats.nass.usda.gov/api
   - Set as environment variable: `export NASS_API_KEY="your_key_here"`

3. **Disk Space**: ~100 MB for data and models

### Quick Setup (Automated)

Run the complete pipeline:

```bash
chmod +x RUN_SOYBEAN_MODERATE_MODEL.sh
./RUN_SOYBEAN_MODERATE_MODEL.sh
```

This script will:
1. Collect data from all sources
2. Merge into unified dataset
3. Engineer features
4. Train model
5. Run validation

**Estimated Time**: 30-60 minutes

### Manual Setup (Step-by-Step)

#### Step 1: Data Collection

```bash
# Prices from Yahoo Finance
python etl/soybean_prices_yahoo.py

# COT positioning from CFTC
python etl/cot_soybean_cftc.py
python etl/cftc_options_soybean.py

# USDA fundamentals
python etl/wasde_soybean_usda.py
python etl/crop_conditions_soybean_nass.py

# Weather data
python etl/weather_nclimgrid.py  # If not already run
python etl/weather_soybean_belt_index.py
```

#### Step 2: Merge Data

```bash
python etl/merge_soybean.py
```

Verify: `data/soybean_combined.csv` should have ~5,000+ rows

#### Step 3: Feature Engineering

```bash
python scripts_soybean/01_feature_engineering.py
```

Verify: `data/soybean_combined_features.csv` should have 179 columns

#### Step 4: Train Model

```bash
python scripts_soybean/train_moderate_soybean.py
```

Output files:
- `models/production/moderate_soybean/model.pkl`
- `models/production/moderate_soybean/imputer.pkl`
- `models/production/moderate_soybean/feature_importance.csv`

#### Step 5: Validate

```bash
python scripts_soybean/validate_moderate_soybean.py
```

Output:
- `validation_results/walk_forward_results.csv`
- Console output with performance metrics

---

## Validation Methodology

### Walk-Forward Validation

**6 Out-of-Sample Periods**:

| Period | Training Data | Test Data | Purpose |
|--------|--------------|-----------|---------|
| 2014-2015 | 2005-2013 | 2014-2015 | Early performance |
| 2016-2017 | 2005-2015 | 2016-2017 | Mid-cycle |
| 2018-2019 | 2005-2017 | 2018-2019 | Pre-COVID |
| 2020-2021 | 2005-2019 | 2020-2021 | COVID volatility |
| 2022-2023 | 2005-2021 | 2022-2023 | Post-COVID |
| 2024-2025 | 2005-2023 | 2024-2025 | Recent performance |

### Validation Criteria

**Pass Requirements**:
- ✅ Sharpe Ratio > 1.0 across all periods
- ✅ Max Drawdown < -15% in any period
- ✅ Win Rate > 60% average
- ✅ Positive returns in >80% of periods

**Ideal Performance**:
- Sharpe > 2.0
- Max DD < -10%
- Win Rate > 70%
- Positive in 100% of periods

### Performance Metrics

For each period, we measure:

1. **Return Metrics**:
   - Total return (period)
   - Annualized return
   - Average trade return
   - Average win vs average loss

2. **Risk Metrics**:
   - Sharpe ratio
   - Max drawdown
   - Volatility of returns
   - Downside deviation

3. **Accuracy Metrics**:
   - Directional accuracy (predicted vs actual direction)
   - Win rate (profitable trades %)
   - Precision/recall for long and short signals

4. **Trading Metrics**:
   - Number of trades
   - Trades per year
   - Longest winning/losing streak
   - Profit factor (gross profit / gross loss)

---

## Comparison to Corn Model

### Architecture Similarities

Both models use:
- XGBoost regression on 10-day forward returns
- 85th/15th percentile entry thresholds
- 20% R per trade position sizing
- 3.5× ATR stops, 2.0R profit targets
- Walk-forward validation on 2014-2025

### Key Differences

| Aspect | Corn | Soybeans |
|--------|------|----------|
| **Ticker** | ZC=F | ZS=F |
| **Contract Size** | 5,000 bushels | 5,000 bushels |
| **Price Multiplier** | $50/point | $50/point |
| **Avg Price** | $4-6 | $10-15 |
| **Contract Value** | $25,000 | $60,000 |
| **Margin** | ~$2,000 | ~$4,500 |
| **Critical Growth** | Jun-Jul pollination | Jul-Aug flowering |
| **Top Producer** | Iowa (27.4%) | Illinois (18.0%) |
| **Weather Sensitivity** | Very high (tasseling) | Very high (pod setting) |
| **USDA Database** | Feed Grains | Oil Crops |

### Expected Performance Comparison

Both should perform similarly on a percentage basis:

| Model | Annual Return | Sharpe | Drawdown | Win Rate |
|-------|--------------|--------|----------|----------|
| **Corn Moderate** | +35% | 3.2 | -10% | 74% |
| **Soybean Moderate** | +35% | 2.5-3.0 | -8% to -10% | 70-75% |

---

## Usage

### Daily Signal Generation

After training and validation, generate daily signals:

```python
import pandas as pd
import joblib
from datetime import datetime

# Load model
model = joblib.load('models/production/moderate_soybean/model.pkl')
imputer = joblib.load('models/production/moderate_soybean/imputer.pkl')

# Load today's features
features = pd.read_csv('data/soybean_combined_features.csv')
today = features[features['date'] == datetime.now().date()].copy()

# Prepare features
X = today[feature_cols]
X_imputed = imputer.transform(X)

# Predict
prediction = model.predict(X_imputed)[0]

# Calculate percentile (using recent 100 days)
recent = features.tail(100)
percentile = (recent['fwd_ret_10d'] < prediction).mean()

# Generate signal
if percentile >= 0.85:
    print(f"LONG signal: Predicted return = {prediction:.3f} (85th+ percentile)")
elif percentile <= 0.15:
    print(f"SHORT signal: Predicted return = {prediction:.3f} (15th- percentile)")
else:
    print(f"NO TRADE: Predicted return = {prediction:.3f} ({percentile:.1%} percentile)")
```

### Position Sizing Example

```python
# Account parameters
account_size = 100000  # $100k
r_per_trade = 0.20     # 20% R
current_price = 12.50  # $/bushel
atr = 0.15             # 15 cents ATR
stop_distance = 3.5 * atr  # 52.5 cents

# Calculate position
risk_amount = account_size * r_per_trade  # $20,000
contract_value = 5000  # bushels per contract
risk_per_contract = stop_distance * contract_value  # $2,625 per contract
num_contracts = int(risk_amount / risk_per_contract)  # 7 contracts

print(f"Position: {num_contracts} contracts")
print(f"Entry: ${current_price:.2f}")
print(f"Stop: ${current_price - stop_distance:.2f}")
print(f"Target: ${current_price + (2.0 * stop_distance):.2f} (2R)")
print(f"Risk: ${num_contracts * risk_per_contract:,.0f}")
```

---

## Monitoring and Maintenance

### Daily Tasks

1. **Update Data**: Run ETL scripts to fetch latest data
2. **Generate Signals**: Run prediction script
3. **Monitor Positions**: Track open trades vs stops/targets
4. **Record Results**: Log actual vs predicted returns

### Weekly Tasks

1. **Review Performance**: Compare actual vs expected metrics
2. **Check Data Quality**: Verify all data sources updating
3. **Rebalance**: Adjust positions if needed

### Monthly Tasks

1. **Performance Report**: Calculate monthly returns, Sharpe, drawdown
2. **Feature Importance**: Check if key features remain predictive
3. **Model Drift Check**: Compare recent accuracy to validation

### Quarterly Tasks

1. **Retrain Model**: Retrain on all available data
2. **Validation Update**: Run validation on recent out-of-sample period
3. **Parameter Review**: Consider adjusting thresholds if needed

### Annual Tasks

1. **Full Backtest**: Re-run complete validation
2. **Architecture Review**: Consider model improvements
3. **Compare to Alternatives**: Benchmark vs buy-and-hold, other models

---

## Risk Warnings

### Market Risks

- **Leverage**: Futures contracts are highly leveraged (20:1+ margin)
- **Volatility**: Commodity prices can move violently on USDA reports, weather events
- **Gaps**: Overnight gaps can bypass stops
- **Liquidity**: Front month contracts may have limited depth

### Model Risks

- **Overfitting**: Model may not perform as well in real trading as in backtest
- **Regime Change**: Market dynamics can shift, reducing predictive power
- **Data Quality**: Errors in weather, USDA, or COT data can lead to bad signals
- **Execution**: Real-world slippage and commissions reduce returns

### Position Sizing Risks

- **20% R is aggressive**: A string of 5 losses = -100% (account wipeout)
- **Drawdowns can exceed estimates**: Models assume independent trades
- **Correlation**: Multiple positions may be correlated (not independent)

### Recommended Risk Management

1. **Start Small**: Begin with 5-10% R per trade until comfortable
2. **Use Stops**: Always set hard stops, never override them
3. **Diversify**: Don't put all capital in soybeans alone
4. **Monitor Closely**: Check positions daily during critical growth periods
5. **Accept Losses**: Some trades will lose - focus on process, not individual outcomes

---

## Appendix

### File Structure

```
ag_analyst/
├── data/
│   ├── soybean_combined.csv              # Merged raw data
│   ├── soybean_combined_features.csv     # 179 engineered features
│   ├── soybean_prices.csv                # Yahoo Finance data
│   ├── cot_soybean.csv                   # CFTC COT data
│   ├── cftc_options_soybean.csv          # CFTC options data
│   ├── wasde_soybean.csv                 # USDA WASDE data
│   ├── crop_conditions_soybean.csv       # NASS crop conditions
│   └── weather_soybean_belt_index.csv    # Weather index
├── etl/
│   ├── soybean_prices_yahoo.py
│   ├── cot_soybean_cftc.py
│   ├── cftc_options_soybean.py
│   ├── wasde_soybean_usda.py
│   ├── crop_conditions_soybean_nass.py
│   ├── weather_soybean_belt_index.py
│   └── merge_soybean.py
├── scripts_soybean/
│   ├── 01_feature_engineering.py
│   ├── train_moderate_soybean.py
│   └── validate_moderate_soybean.py
└── models/production/moderate_soybean/
    ├── model.pkl                          # Trained XGBoost model
    ├── imputer.pkl                        # Feature imputer
    ├── feature_importance.csv             # Feature rankings
    ├── feature_names.json                 # Feature list
    ├── training_metadata.json             # Training info
    ├── model_config.json                  # Configuration
    ├── DOCUMENTATION.md                   # This file
    └── validation_results/
        └── walk_forward_results.csv       # Validation metrics
```

### Troubleshooting

**Issue**: Not enough training data
- **Solution**: Ensure `soybean_combined_features.csv` has >3,000 rows with data back to 2005

**Issue**: Poor validation performance
- **Solution**: Check data quality, try adjusting hyperparameters, extend training window

**Issue**: Too few signals generated
- **Solution**: Consider widening thresholds (80th/20th instead of 85th/15th)

**Issue**: High drawdowns in validation
- **Solution**: Reduce R per trade (try 10-15% R), tighten stops, or add regime filtering

---

**Documentation Version**: 1.0
**Last Updated**: 2025-11-16
**Next Review**: After validation complete
