# Quick Start Guide

Get up and running with AG Futures Production in 5 minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- ~30 MB disk space for data

## Setup (First Time Only)

### 1. Install Dependencies

```bash
cd ag-futures-prod
pip install -r requirements.txt
```

**Time**: 2-3 minutes

### 2. Verify Data Files

Check that data files exist:

```bash
ls data/
```

You should see:
- `corn_combined_features.csv` (8.6 MB)
- `soybean_combined_features.csv` (8.6 MB)
- Other data files (prices, COT, WASDE, weather, etc.)

If data files are missing, you'll need to run the initial data collection (see below).

### 3. Test Signal Generation

```bash
python scripts/generate_signals.py
```

You should see output like:

```
🌽 CORN FUTURES - DAILY SIGNAL
================================================================================
Date: 2025-11-18
Model: Moderate (20% R)

📊 Signal: LONG
   Confidence: 72.0% (Percentile: 85.3%)

📈 Entry:
   Price: $4.50
   Position Size: 20.0% of equity

🎯 Risk Management:
   Stop Loss: $4.15 (3.5x ATR)
   Profit Target: $5.20 (2.0R)
   Time Stop: 2025-11-28 (10 days)
```

**Time**: 30 seconds

## Daily Usage

### Update Data and Generate Signals

```bash
# 1. Update all data (both corn and soybeans)
python scripts/update_all.py

# 2. Generate trading signals
python scripts/generate_signals.py
```

**Total Time**: 2-3 minutes

### Update Only One Commodity

```bash
# Corn only
python scripts/update_all.py --corn-only

# Soybeans only
python scripts/update_all.py --soy-only
```

## Initial Data Collection (If Needed)

If you're starting fresh without existing data files:

### Corn Data Collection

```bash
# 1. Fetch price data (1-2 minutes)
python etl/corn_prices_yahoo.py

# 2. Fetch sentiment and fundamentals (~5 minutes)
python etl/cot_corn_cftc.py
python etl/cftc_options_corn.py
python etl/wasde_corn_usda.py
python etl/crop_conditions_nass.py

# 3. Fetch weather data (~10 minutes)
python etl/weather_openmeteo.py --corn-only

# 4. Merge all data sources
python etl/merge_corn_wrapper.py

# 5. Generate features
python features/corn_features.py
```

**Total Time**: ~20 minutes

### Soybean Data Collection

```bash
# Same process for soybeans
python etl/soybean_prices_yahoo.py
python etl/cot_soybean_cftc.py
python etl/cftc_options_soybean.py
python etl/wasde_soybean_usda.py
python etl/crop_conditions_soybean_nass.py
python etl/weather_openmeteo.py --soy-only
python etl/merge_soybean_wrapper.py
python features/soybean_features.py
```

**Total Time**: ~20 minutes

## Verification

### Check Data Quality

```bash
python scripts/verify_data.py
```

Output shows:
- Latest data date
- Latest price
- Number of rows
- Data freshness warning if > 5 days old

### Check Current Signal Percentiles

Edit `scripts/generate_signals.py` to add debug output, or check the CSV:

```bash
# View signal history
cat signals/signal_history.csv
```

## Troubleshooting

### Issue: "FileNotFoundError: corn_combined_features.csv"

**Solution**: Run the data pipeline first:

```bash
python scripts/update_all.py --corn-only
```

### Issue: "ModuleNotFoundError: No module named 'xgboost'"

**Solution**: Install dependencies:

```bash
pip install -r requirements.txt
```

### Issue: Data is stale (> 5 days old)

**Solution**: Update the data pipeline:

```bash
python scripts/update_all.py
```

### Issue: Model file not found

**Solution**: Ensure model files exist in `models/*/`:
- `model.pkl`
- `scaler.pkl` or `imputer.pkl`
- `model_config.json`

If missing, copy from the original ag_analyst repository.

## Next Steps

Once you have signals running:

1. **Review [TRADING_GUIDE.md](TRADING_GUIDE.md)** - Learn how to use signals
2. **Read [MODELS.md](MODELS.md)** - Understand each model's strategy
3. **Check [DATA_SOURCES.md](DATA_SOURCES.md)** - Learn about data sources
4. **Set up automation** - Use GitHub Actions or cron jobs for daily updates

## Summary

**Minimum Daily Workflow**:

```bash
# Morning: Update data
python scripts/update_all.py

# Review signals
python scripts/generate_signals.py

# Execute trades based on signals
```

**Time**: 3-5 minutes per day

---

For detailed information, see the main [README.md](../README.md).
