# AG Futures Production

Production-ready machine learning system for trading corn and soybean futures. This repository contains only validated models, production data pipelines, and essential scripts for daily trading operations.

## What This System Does

**Generates Daily Trading Signals** for corn and soybean futures using:
- 6 validated machine learning models (XGBoost regression)
- 20+ years of historical data (2005-present)
- 160-180 engineered features per commodity
- Automated data updates and feature engineering

**Data Sources**:
- Yahoo Finance: Daily OHLCV price data
- CFTC: Weekly Commitment of Traders (futures + options)
- USDA WASDE: Monthly supply/demand fundamentals
- USDA NASS: Weekly crop condition ratings
- Open-Meteo: Daily weather data (2-day lag)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Daily Update Pipeline

```bash
# Update all data and features
python scripts/update_all.py

# Or update individually
python scripts/update_all.py --corn-only
python scripts/update_all.py --soy-only
```

### 3. Generate Trading Signals

```bash
python scripts/generate_signals.py
```

Output example:
```
Signal: LONG
Confidence: 72%
Entry: $4.50
Stop Loss: $4.15 (3.5x ATR)
Profit Target: $5.20 (2.0R)
Position Size: 20% of equity
```

## Production Models

All models in `models/` are production-ready with validated backtests.

### Corn Models

| Model | Strategy | Sharpe | Win Rate | Max DD | Files |
|-------|----------|--------|----------|--------|-------|
| **moderate** | Balanced (20% R per trade) | 0.52-0.85 | 65-72% | -12% | 19 |
| **growth** | Aggressive (30% R) | 0.45-0.78 | 63-68% | -18% | 5 |
| **corn_high_conviction** | Selective (90th percentile) | 5.80 | 75% | TBD | 6 |
| **conservative_v2.0** | Low-risk (pending validation) | TBD | TBD | TBD | 3 |

### Soybean Models

| Model | Strategy | Sharpe | Win Rate | Max DD | Files |
|-------|----------|--------|----------|--------|-------|
| **moderate_soybean** | Balanced (20% R) | 0.45-0.72 | 62-68% | -15% | 10 |
| **soy_high_conviction** | Selective (90th percentile) | 3.82 | 79% | TBD | 6 |

Each model directory contains:
- `model.pkl`: Trained XGBoost model
- `scaler.pkl` / `imputer.pkl`: Preprocessing artifacts
- `model_config.json`: Model parameters
- `README.md` or `DOCUMENTATION.md`: Model details
- `validation_results/`: Performance metrics

## Repository Structure

```
ag-futures-prod/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
│
├── data/                        # Data files (~27 MB total)
│   ├── corn_combined_features.csv     (8.6 MB, 180 features)
│   ├── soybean_combined_features.csv  (8.6 MB, 180 features)
│   ├── corn_prices.csv                (0.3 MB, daily OHLCV)
│   ├── soybean_prices.csv             (0.3 MB)
│   ├── cot_*.csv                      (weekly sentiment)
│   ├── cftc_options_*.csv             (weekly options)
│   ├── wasde_*.csv                    (monthly fundamentals)
│   ├── crop_conditions*.csv           (weekly ratings)
│   └── weather_*_belt_index.csv       (daily weather)
│
├── etl/                         # Data collection scripts (15 files)
│   ├── corn_prices_yahoo.py           # Fetch daily prices
│   ├── soybean_prices_yahoo.py
│   ├── cot_corn_cftc.py               # CFTC sentiment data
│   ├── cot_soybean_cftc.py
│   ├── cftc_options_*.py              # Options positioning
│   ├── wasde_*.py                     # USDA fundamentals
│   ├── crop_conditions_*.py           # Crop ratings
│   ├── weather_openmeteo.py           # Weather data
│   ├── merge_corn.py                  # Merge data sources
│   └── merge_soybean.py
│
├── features/                    # Feature engineering
│   ├── corn_features.py               # Generate corn features (180 cols)
│   └── soybean_features.py            # Generate soybean features
│
├── models/                      # Production models (6 models, 49 files)
│   ├── moderate/                      # Corn balanced strategy
│   ├── growth/                        # Corn growth strategy
│   ├── corn_high_conviction/          # Corn high-confidence
│   ├── conservative_v2.0/             # Corn conservative (pending)
│   ├── moderate_soybean/              # Soybean balanced
│   └── soy_high_conviction/           # Soybean high-confidence
│
├── scripts/                     # Core operational scripts
│   ├── update_all.py                  # Master data pipeline
│   ├── generate_signals.py            # Daily signal generation
│   ├── verify_data.py                 # Data quality checks
│   └── retrain_models.py              # Model retraining (stub)
│
├── signals/                     # Signal outputs
│   └── signal_history.csv             # Historical signals log
│
├── docs/                        # Documentation
│   ├── QUICKSTART.md                  # 5-minute setup guide
│   ├── DATA_SOURCES.md                # Data documentation
│   ├── MODELS.md                      # Model details
│   └── TRADING_GUIDE.md               # How to use signals
│
└── .github/workflows/           # CI/CD automation
    └── daily_update.yml               # Automated daily updates
```

**Total Files**: ~60 production files (vs 150+ in original repo)

## Daily Workflow

### Recommended Schedule

**Every Trading Day** (after market close):
1. Run `python scripts/update_all.py` to update data
2. Run `python scripts/generate_signals.py` to get signals
3. Review signals and execute trades

**Weekly** (optional):
- Review signal performance
- Check data quality with `python scripts/verify_data.py`

**Monthly** (optional):
- Consider retraining models if significant new data accumulated
- Review model performance metrics

### Data Update Pipeline

The `update_all.py` script runs a 3-stage pipeline:

```
Stage 1: Fetch Latest Data
├─ Yahoo Finance → corn_prices.csv
├─ CFTC → cot_corn.csv (weekly)
├─ USDA → wasde_corn.csv (monthly)
└─ Open-Meteo → weather_corn_belt_index.csv

Stage 2: Merge Data Sources
└─ etl/merge_corn.py → corn_combined.csv (77 columns)

Stage 3: Feature Engineering
└─ features/corn_features.py → corn_combined_features.csv (180 columns)

Models & Scripts
└─ Read from: *_combined_features.csv
```

**Important**: Always run all 3 stages. Models read from `*_combined_features.csv`.

## Model Configuration

Each model has a `model_config.json` specifying:

```json
{
  "parameters": {
    "thresholds": {
      "long_percentile": 0.80,
      "short_percentile": 0.20,
      "rolling_window": 100
    },
    "position_sizing": {
      "r_per_trade": 0.20
    },
    "stops": {
      "atr_multiplier": 3.5,
      "atr_period": 20,
      "time_stop_days": 10
    },
    "profit_targets": {
      "target_r": 2.0
    }
  }
}
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Optional API keys (for initial data collection)
NOAA_API_TOKEN=your_token_here
USDA_NASS_API_KEY=your_key_here

# Trading account (optional)
ACCOUNT_SIZE=100000
MAX_PORTFOLIO_RISK=0.20
```

## Validation Status

| Model | Training Data | Test Period | Status |
|-------|---------------|-------------|--------|
| Corn Moderate | 2005-2023 | 2024-2025 | ✅ Validated |
| Corn Growth | 2005-2023 | 2024-2025 | ✅ Validated |
| Corn High Conviction | 2005-2023 | 2024-2025 | ✅ Validated |
| Soybean Moderate | 2005-2023 | 2024-2025 | ✅ Validated |
| Soy High Conviction | 2005-2023 | 2024-2025 | ✅ Validated |
| Conservative v2.0 | TBD | TBD | ⏳ Pending |

## Key Differences from Original Repo

This production repo has been **streamlined** for daily operations:

**Removed**:
- ❌ Experimental models and features
- ❌ Inactive/archived code (33+ legacy scripts)
- ❌ Research notebooks and analysis scripts
- ❌ 25+ documentation files (consolidated to 4)
- ❌ Streamlit dashboard (TBD separate deployment)
- ❌ Non-essential dependencies (matplotlib, seaborn, shap, hmmlearn)

**Reorganized**:
- ✅ Feature engineering moved from `inactive/scripts/` to `features/`
- ✅ Models moved from `models/production/` to `models/`
- ✅ Scripts renamed for clarity
- ✅ Documentation consolidated into `docs/`

**Simplified**:
- ✅ 60% fewer files (60 vs 150+)
- ✅ 85% less documentation (4 vs 30+ files)
- ✅ 40% lighter dependencies (12 vs 20 packages)
- ✅ Clear separation of concerns (ETL / Features / Models / Scripts)

## Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute setup guide
- **[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)** - Data documentation
- **[docs/MODELS.md](docs/MODELS.md)** - Model architecture and performance
- **[docs/TRADING_GUIDE.md](docs/TRADING_GUIDE.md)** - How to use trading signals

## Support & Development

This is the **production deployment** of the ag_analyst project. For:
- Model development and experimentation
- Historical research and backtesting
- Feature engineering exploration
- Model retraining scripts

Refer to the original `ag_analyst` repository.

## Disclaimer

**Past performance does not guarantee future results.** Trading futures involves substantial risk of loss. Only trade with capital you can afford to lose. This software is for educational purposes. Not financial advice.

---

**Version**: 1.0.0
**Last Updated**: November 2025
**Production Models**: 6 (5 validated, 1 pending)
**Data Coverage**: 2005-present (20+ years)
