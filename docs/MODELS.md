# Production Models Documentation

Complete guide to the 6 production models in AG Futures Production.

## Overview

All models use **XGBoost regression** to predict 10-day forward returns, then convert predictions to BUY/SELL/HOLD signals based on percentile thresholds.

**Model Framework**:
```
Input: 160-180 engineered features
│
├─ XGBoost Model → Predicted 10-day return
├─ Rolling percentile (100-day window)
│
Decision Logic:
├─ IF percentile > 80th → LONG signal
├─ IF percentile < 20th → SHORT signal
└─ ELSE → HOLD (no trade)
```

---

## Model Lineup

| Model | Asset | Strategy | R/Trade | Sharpe | Win Rate | Status |
|-------|-------|----------|---------|--------|----------|--------|
| **moderate** | Corn | Balanced | 20% | 0.52-0.85 | 65-72% | ✅ Active |
| **growth** | Corn | Aggressive | 30% | 0.45-0.78 | 63-68% | ✅ Active |
| **corn_high_conviction** | Corn | Selective | Var | 5.80 | 75% | ✅ Active |
| **moderate_soybean** | Soybean | Balanced | 20% | 0.45-0.72 | 62-68% | ✅ Active |
| **soy_high_conviction** | Soybean | Selective | Var | 3.82 | 79% | ✅ Active |
| **conservative_v2.0** | Corn | Low-Risk | 10-15% | TBD | TBD | ⏳ Pending |

---

## 1. Corn Moderate Model

**Directory**: `models/moderate/`

### Strategy

Balanced risk/reward model suitable for growth-oriented traders.

**Key Parameters**:
- **Position Size**: 20% R per trade
- **Entry Thresholds**: 80th/20th percentile
- **Profit Target**: 2.0R
- **Stop Loss**: 3.5× ATR
- **Time Stop**: 10 days

### Performance (2024-2025 Test Period)

| Metric | Value |
|--------|-------|
| **Sharpe Ratio** | 0.52 - 0.85 |
| **Win Rate** | 65 - 72% |
| **Avg Return/Trade** | +1.8% to +2.4% |
| **Max Drawdown** | -12% |
| **Annual Return** | ~30-35% |

### Use Cases

**✅ Ideal For**:
- Growth-focused portfolios
- Traders with $120K+ capital
- Moderate risk tolerance (-10% to -15% DD acceptable)
- Core allocation (60-70% of corn position)

**❌ Not Ideal For**:
- Cannot handle -10% drawdowns → Use conservative
- Seeking maximum returns → Use growth or high conviction
- Under-capitalized (< $60K)

### Files

```
models/moderate/
├── model.pkl (10.2 MB)         # XGBoost model
├── scaler.pkl (0.1 MB)         # RobustScaler
├── imputer.pkl (0.1 MB)        # SimpleImputer
├── model_config.json           # Parameters
├── DOCUMENTATION.md            # Full docs
├── VALIDATION_RESULTS.md       # Performance analysis
└── validation_results/         # Detailed metrics (12 files)
```

---

## 2. Corn Growth Model

**Directory**: `models/growth/`

### Strategy

Aggressive growth-oriented model for higher returns with higher risk.

**Key Parameters**:
- **Position Size**: 30% R per trade (vs 20% moderate)
- **Entry Thresholds**: 75th/25th percentile (more trades)
- **Profit Target**: 2.5R (vs 2.0R moderate)
- **Stop Loss**: 4.0× ATR (vs 3.5× moderate)
- **Time Stop**: 10 days

### Performance (2024-2025 Test Period)

| Metric | Value |
|--------|-------|
| **Sharpe Ratio** | 0.45 - 0.78 |
| **Win Rate** | 63 - 68% |
| **Avg Return/Trade** | +2.1% to +3.2% |
| **Max Drawdown** | -18% |
| **Annual Return** | ~60% |

### Use Cases

**✅ Ideal For**:
- Aggressive growth seekers
- Higher risk tolerance (-15% to -20% DD acceptable)
- Traders with $150K+ capital
- Satellite allocation (20-30% of corn position)

**❌ Not Ideal For**:
- Risk-averse traders
- Seeking sleep-at-night factor
- Cannot tolerate -20% swings

### Files

```
models/growth/
├── model.pkl                   # XGBoost model
├── scaler.pkl
├── imputer.pkl
├── model_config.json
├── DOCUMENTATION.md
└── validation_results/         # Detailed metrics (3 files)
```

---

## 3. Corn High Conviction Model

**Directory**: `models/corn_high_conviction/`

### Strategy

Selective model that only trades **top 10% / bottom 10%** of predictions. Quality over quantity.

**Key Parameters**:
- **Entry Thresholds**: 90th/10th percentile (very selective)
- **Position Size**: Varies by conviction (10-30% R)
- **Profit Target**: None (let winners run)
- **Stop Loss**: 3.5× ATR
- **Time Stop**: 10 days

### Performance (2024-2025 Test Period)

| Metric | Value |
|--------|-------|
| **Sharpe Ratio** | 5.80 (exceptional) |
| **Win Rate** | 75.3% |
| **Trade Frequency** | ~117 trades/year |
| **Avg Return/Trade** | +3-5% (estimated) |

### Use Cases

**✅ Ideal For**:
- High-conviction traders
- Selective signal execution
- Complementing other models
- Overlay on existing positions

**❌ Not Ideal For**:
- Want frequent trades (only ~10/month)
- Need steady signals

### Files

```
models/corn_high_conviction/
├── model.pkl                   # XGBoost model
├── imputer.pkl
├── model_config.json
├── feature_names.json
├── feature_importance.csv
└── training_metadata.json
```

---

## 4. Soybean Moderate Model

**Directory**: `models/moderate_soybean/`

### Strategy

Balanced soybean strategy, analogous to corn moderate but optimized for soybeans.

**Key Parameters**:
- **Position Size**: 20% R per trade
- **Entry Thresholds**: 80th/20th percentile
- **Profit Target**: 2.0R
- **Stop Loss**: 3.5× ATR
- **Time Stop**: 10 days

### Performance (2024-2025 Test Period)

| Metric | Value |
|--------|-------|
| **Sharpe Ratio** | 0.45 - 0.72 |
| **Win Rate** | 62 - 68% |
| **Avg Return/Trade** | +1.6% to +2.2% |
| **Max Drawdown** | -15% |
| **Annual Return** | ~30% |

### Use Cases

**✅ Ideal For**:
- Diversifying from corn
- Soybean-specific traders
- Balanced portfolio construction
- Moderate risk tolerance

### Files

```
models/moderate_soybean/
├── model.pkl                   # XGBoost model
├── imputer.pkl
├── model_config.json
├── DOCUMENTATION.md
├── VALIDATION_SUMMARY.md
├── SETUP_STATUS.md
├── feature_names.json
├── feature_importance.csv
├── training_metadata.json
└── validation_results/         # Detailed metrics
```

---

## 5. Soybean High Conviction Model

**Directory**: `models/soy_high_conviction/`

### Strategy

Selective soybean model, only top/bottom 10% of predictions.

**Key Parameters**:
- **Entry Thresholds**: 90th/10th percentile
- **Position Size**: Varies (10-30% R)
- **Profit Target**: None
- **Stop Loss**: 3.5× ATR
- **Time Stop**: 10 days

### Performance (2024-2025 Test Period)

| Metric | Value |
|--------|-------|
| **Sharpe Ratio** | 3.82 (excellent) |
| **Win Rate** | 78.8% |
| **Trade Frequency** | ~114 trades/year |

### Use Cases

**✅ Ideal For**:
- High-conviction soybean traders
- Selective execution
- Quality over quantity approach

### Files

```
models/soy_high_conviction/
├── model.pkl                   # XGBoost model
├── imputer.pkl
├── model_config.json
├── feature_names.json
├── feature_importance.csv
└── training_metadata.json
```

---

## 6. Conservative v2.0 Model (Pending Validation)

**Directory**: `models/conservative_v2.0/`

### Strategy

Low-risk defensive model for risk-averse traders.

**Key Parameters**:
- **Position Size**: 10-15% R per trade (TBD)
- **Entry Thresholds**: 90th/10th percentile (selective)
- **Profit Target**: TBD
- **Stop Loss**: 3.0× ATR (tighter)
- **Time Stop**: 10 days

### Expected Performance

| Metric | Target |
|--------|--------|
| **Sharpe Ratio** | > 1.5 |
| **Win Rate** | > 60% |
| **Max Drawdown** | < -8% |
| **Annual Return** | ~18-25% |

### Status

⏳ **Pending Validation**

This model needs to be validated before production use. Run validation in the original ag_analyst repository, then copy updated model files here.

### Files

```
models/conservative_v2.0/
├── model_config.json           # Parameters defined
└── validation_results/         # Validation CSV (empty)
```

---

## Model Training Details

### Common Configuration

All models share this XGBoost configuration:

```python
XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
```

### Training Data

- **Period**: 2005-2023 (18 years)
- **Samples**: ~4,500 daily observations
- **Features**: 160-180 engineered features
- **Target**: `fwd_ret_10d` (10-day forward returns)
- **Validation**: Walk-forward methodology (6 periods)

### Preprocessing

1. **Imputation**: SimpleImputer (median strategy)
2. **Scaling**: RobustScaler (robust to outliers)
3. **Feature Selection**: Drop columns with > 80% missing values

### Validation Methodology

**Walk-Forward Testing** (6 periods):
- 2014-2015
- 2016-2017
- 2018-2019
- 2020-2021 (COVID stress test)
- 2022-2023
- 2024-2025 (true out-of-sample)

---

## Choosing a Model

### Decision Matrix

| Your Priority | Recommended Model |
|---------------|-------------------|
| **Maximum Returns** | Growth or High Conviction |
| **Balanced Growth** | Moderate (corn or soy) |
| **Low Risk** | Conservative v2.0 (pending) |
| **High Win Rate** | High Conviction models |
| **Frequent Signals** | Moderate or Growth |
| **Selective Trades** | High Conviction |
| **Sleep Well** | Conservative v2.0 or Moderate |

### Portfolio Approach

Consider using **multiple models**:

**Example Allocation**:
- 60% Moderate (core, balanced)
- 20% Conservative (stability)
- 20% High Conviction (upside)

**Benefits**:
- Diversified strategies
- Smoother equity curve
- Reduce single-model risk

---

## Model Files Explained

Each model directory contains:

### Core Files (Required)

| File | Purpose | Size |
|------|---------|------|
| `model.pkl` | Trained XGBoost model | 5-10 MB |
| `scaler.pkl` or `imputer.pkl` | Preprocessing artifacts | < 1 MB |
| `model_config.json` | Model parameters | < 10 KB |

### Documentation Files

| File | Purpose |
|------|---------|
| `DOCUMENTATION.md` | Model design and strategy |
| `VALIDATION_RESULTS.md` | Performance analysis |
| `README.md` | Quick reference |

### Metadata Files (Optional)

| File | Purpose |
|------|---------|
| `feature_names.json` | List of features used |
| `feature_importance.csv` | Feature importance rankings |
| `training_metadata.json` | Training date, params, etc. |

### Validation Results

| File | Purpose |
|------|---------|
| `validation_results/all_trades.csv` | Every trade executed |
| `validation_results/walk_forward_results.csv` | Period-by-period metrics |
| `validation_results/*.csv` | Additional analysis |

---

## Feature Importance

Top features across all models:

1. **Crop Condition Index** (pct_good_excellent)
2. **WASDE Stocks-to-Use Ratio**
3. **Put/Call Ratio Percentile**
4. **Money Manager Net Position**
5. **20-day Moving Average**
6. **GDD Anomaly** (growing degree days vs normal)
7. **RSI (14-day)**
8. **MACD Signal**
9. **ATR Volatility**
10. **Seasonal indicators** (day of year, month)

---

## Retraining Models

Models should be retrained:
- **Monthly** (if significant new data)
- **Quarterly** (routine maintenance)
- **After major market events** (e.g., drought, supply shock)

**Process**:
1. Update all data (run `scripts/update_all.py`)
2. Train new model in original ag_analyst repo
3. Validate performance (walk-forward, stress tests)
4. Copy new model files to `models/*/`
5. Test signal generation
6. Deploy

**Note**: Retraining script (`scripts/retrain_models.py`) is currently a stub. Use the original ag_analyst repository for model training.

---

## Model Performance Tracking

### Signal History

All signals logged to `signals/signal_history.csv`:

```csv
date,signal,confidence,prediction,percentile,current_price,stop_loss,profit_target,position_size_pct,atr,time_stop_date
2025-11-18,LONG,0.72,0.023,0.853,4.50,4.15,5.20,20.0,0.10,2025-11-28
```

### Analyzing Performance

```python
import pandas as pd

signals = pd.read_csv('signals/signal_history.csv', parse_dates=['date'])

# Win rate
signals['outcome'] = (signals['signal'] == 'LONG') & (signals['actual_return'] > 0)
win_rate = signals['outcome'].mean()

# Average return
avg_return = signals['actual_return'].mean()

# Sharpe ratio
sharpe = signals['actual_return'].mean() / signals['actual_return'].std() * (252**0.5)
```

---

## Support & Issues

For model-related questions:
- Review `models/*/DOCUMENTATION.md`
- Check `models/*/VALIDATION_RESULTS.md`
- Refer to original ag_analyst repository for training scripts

---

For next steps, see [TRADING_GUIDE.md](TRADING_GUIDE.md).
