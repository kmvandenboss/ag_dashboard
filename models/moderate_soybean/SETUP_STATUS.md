# Moderate Soybean Model - Setup Status

**Created**: 2025-11-16
**Status**: ⚠️ **DATA COLLECTION REQUIRED**

---

## Current Status

### ✅ Completed

1. **Model Architecture Created**
   - Training script: `scripts_soybean/train_moderate_soybean.py`
   - Validation script: `scripts_soybean/validate_moderate_soybean.py`
   - Configuration: `models/production/moderate_soybean/model_config.json`

2. **Data Pipeline Scripts Created**
   - All 7 ETL scripts for soybean data collection
   - Weather weighting adjusted for soybean production states
   - Feature engineering script adapted for soybeans

3. **Model Configuration Defined**
   - 20% R per trade (matching corn Moderate model)
   - 85th/15th percentile entry thresholds
   - 3.5× ATR stop loss
   - 2.0R profit target
   - XGBoost regression on 10-day forward returns

### ⚠️ Blocked: Data Collection

**Issue**: Soybean data collection incomplete
- Current data: Only 11 rows (demo data)
- Required: ~5,000+ rows of historical data (2005-present)
- Blocker: API access restrictions in current environment
  - Yahoo Finance: 403 Forbidden
  - CFTC: 403 Forbidden
  - USDA/NASS: Requires API key and network access

**Required Data Sources**:
1. ✅ Yahoo Finance (ZS=F) - Script created, needs execution
2. ✅ CFTC COT (Soybeans) - Script created, needs execution
3. ✅ CFTC Options (Soybeans) - Script created, needs execution
4. ✅ USDA WASDE (Soybeans) - Script created, needs execution
5. ✅ NASS Crop Conditions - Script created, needs execution
6. ✅ Weather (Soybean Belt) - Script created, needs execution
7. ✅ Data Merge - Script created, needs execution

### ⏳ Pending (After Data Collection)

1. **Run Feature Engineering**
   ```bash
   python scripts_soybean/01_feature_engineering.py
   ```
   - Will create 179-feature dataset from 76 base columns
   - Adds soybean-specific growing season indicators
   - Creates forward returns, volatility, sentiment features

2. **Train Model**
   ```bash
   python scripts_soybean/train_moderate_soybean.py
   ```
   - Trains XGBoost regressor on 10-day forward returns
   - Uses all data up to 2023-12-31
   - Saves model artifacts to `models/production/moderate_soybean/`

3. **Validate Model**
   ```bash
   python scripts_soybean/validate_moderate_soybean.py
   ```
   - 6 walk-forward periods (2014-2025)
   - Tests out-of-sample performance
   - Generates validation report

4. **Compare to Corn Model**
   - Side-by-side performance metrics
   - Identify commodity-specific patterns
   - Adjust parameters if needed

---

## Data Collection Instructions

### Option 1: Run in Environment with API Access

Execute these scripts in sequence:

```bash
# Step 1: Collect all data sources
python etl/soybean_prices_yahoo.py
python etl/cot_soybean_cftc.py
python etl/cftc_options_soybean.py
python etl/wasde_soybean_usda.py
python etl/crop_conditions_soybean_nass.py
python etl/weather_soybean_belt_index.py

# Step 2: Merge into unified dataset
python etl/merge_soybean.py

# Step 3: Feature engineering
python scripts_soybean/01_feature_engineering.py

# Step 4: Train model
python scripts_soybean/train_moderate_soybean.py

# Step 5: Validate
python scripts_soybean/validate_moderate_soybean.py
```

### Option 2: Manual Data Transfer

If data must be collected elsewhere:

1. Run ETL scripts on a system with API access
2. Copy generated CSV files to this environment:
   - `data/soybean_prices.csv`
   - `data/cot_soybean.csv`
   - `data/cftc_options_soybean.csv`
   - `data/wasde_soybean.csv`
   - `data/crop_conditions_soybean.csv`
   - `data/weather_soybean_belt_index.csv`
3. Run merge: `python etl/merge_soybean.py`
4. Continue with feature engineering and model training

---

## Expected Results (After Full Data Collection)

Based on corn Moderate model performance, we expect:

| Metric | Expected Range |
|--------|---------------|
| **Directional Accuracy** | 65-75% |
| **Win Rate** | 65-75% |
| **Sharpe Ratio** | 2.0-3.0 |
| **Annual Return** | 25-40% |
| **Max Drawdown** | -8% to -12% |
| **Trades/Year** | 70-100 |

---

## Files Created

### Model Files
- `model_config.json` - Model configuration and parameters
- `SETUP_STATUS.md` - This file

### Training Scripts
- `scripts_soybean/train_moderate_soybean.py` - Model training
- `scripts_soybean/validate_moderate_soybean.py` - Walk-forward validation

### ETL Scripts (All Created, Need Execution)
- `etl/soybean_prices_yahoo.py`
- `etl/cot_soybean_cftc.py`
- `etl/cftc_options_soybean.py`
- `etl/wasde_soybean_usda.py`
- `etl/crop_conditions_soybean_nass.py`
- `etl/weather_soybean_belt_index.py`
- `etl/merge_soybean.py`
- `scripts_soybean/01_feature_engineering.py`

---

## Next Actions Required

1. **Execute data collection pipeline** in environment with API/network access
2. **Verify data quality**: ~5,000+ rows with populated features
3. **Run feature engineering**: Create 179-feature dataset
4. **Train model**: Execute training script
5. **Validate model**: Run walk-forward validation
6. **Compare to corn**: Analyze performance differences

---

## Comparison: Corn vs Soybean (Current Status)

| Aspect | Corn Moderate | Soybean Moderate |
|--------|---------------|------------------|
| **Data Rows** | 5,251 ✅ | 11 ⚠️ (needs collection) |
| **Model Trained** | ✅ Yes | ❌ No (insufficient data) |
| **Validation** | ✅ Complete | ⏳ Pending data |
| **Scripts Ready** | ✅ Yes | ✅ Yes |
| **Performance** | 74% dir acc, 3.2 Sharpe | ⏳ TBD |

---

**Summary**: All model architecture and scripts are ready. Model training and validation blocked on data collection due to API access restrictions. Once data is collected (requires ~1 hour with API access), training and validation can proceed immediately.
