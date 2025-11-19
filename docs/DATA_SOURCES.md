# Data Sources Documentation

Complete reference for all data sources used in the AG Futures Production system.

## Overview

The system integrates **7 data sources** covering:
- Daily price data (20+ years)
- Weekly sentiment and positioning
- Monthly supply/demand fundamentals
- Weekly crop conditions
- Daily weather data

All data is **free** and **publicly available**.

---

## 1. Yahoo Finance (Price Data)

**What**: Daily OHLCV (Open, High, Low, Close, Volume) price data

**Source**: Yahoo Finance API via `yfinance` library

**Coverage**: 2005-present (~5,250 daily observations)

**Tickers**:
- **ZC=F**: Corn futures (CBOT)
- **ZS=F**: Soybean futures (CBOT)

**Update Frequency**: Daily (after market close, ~4 PM ET)

**Features Generated**: 6
- `open`, `high`, `low`, `close`, `volume`, `adj_close`

**Scripts**:
- `etl/corn_prices_yahoo.py`
- `etl/soybean_prices_yahoo.py`

**Example Usage**:
```bash
python etl/corn_prices_yahoo.py
# Outputs: data/corn_prices.csv (270 KB, ~5,250 rows)
```

**Data Quality**: Very high. Rare missing days (holidays, exchange closures).

---

## 2. CFTC Commitment of Traders (Sentiment)

**What**: Weekly positioning data from CFTC Disaggregated Futures reports

**Source**: CFTC website ([https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm))

**Coverage**:
- **Corn**: 2013-present (~640 weekly reports)
- **Soybeans**: 2013-present

**Update Frequency**: Weekly (released Friday ~3:30 PM ET, data as of Tuesday close)

**Trader Categories**:
- **Producer/Merchant/Processor**: Commercial hedgers
- **Swap Dealers**: Banks and financial institutions
- **Money Managers**: Hedge funds and CTAs (trend followers)
- **Other Reportables**: Large traders not fitting above categories

**Features Generated**: 20
- Net positions (long - short) for each category
- Percentile ranks (52-week rolling)
- Positioning changes (week-over-week)
- Concentration metrics

**Scripts**:
- `etl/cot_corn_cftc.py`
- `etl/cot_soybean_cftc.py`

**Example Usage**:
```bash
python etl/cot_corn_cftc.py
# Outputs: data/cot_corn.csv (140 KB, ~640 rows)
```

**Trading Insight**:
- **Money Manager positioning extremes** often signal reversals (contrarian indicator)
- **Producer/Merchant hedging** validates supply concerns

---

## 3. CFTC Options Positioning

**What**: Weekly options positioning (futures + options combined)

**Source**: CFTC Traders in Financial Futures (TFF) reports

**Coverage**: 2017-present (~456 weekly reports)

**Update Frequency**: Weekly (released Friday with COT data)

**Features Generated**: 12
- **Put/Call ratios**: Sentiment indicator
- **Net delta positioning**: Equivalent futures exposure
- **Options open interest**: Market participation
- **Percentile ranks**: 52-week rolling context

**Scripts**:
- `etl/cftc_options_corn.py`
- `etl/cftc_options_soybean.py`

**Example Usage**:
```bash
python etl/cftc_options_corn.py
# Outputs: data/cftc_options_corn.csv (85 KB, ~456 rows)
```

**Trading Insight**:
- **Put/Call ratio > 80th percentile**: Extreme fear (potential buy)
- **Put/Call ratio < 20th percentile**: Extreme greed (potential sell)

---

## 4. USDA WASDE (Fundamentals)

**What**: Monthly World Agricultural Supply and Demand Estimates

**Source**: USDA website ([https://www.usda.gov/oce/commodity/wasde](https://www.usda.gov/oce/commodity/wasde))

**Coverage**: 2005-present (~252 monthly reports)

**Update Frequency**: Monthly (usually 2nd Friday of the month, 12 PM ET)

**Data Included**:
- **Production**: Harvested acres × yield
- **Consumption**: Domestic use (feed, food, fuel, exports)
- **Ending Stocks**: Inventory carryover to next year
- **Stocks-to-Use Ratio**: Key supply/demand balance metric

**Features Generated**: 15
- Stocks-to-use ratio (tight = bullish, abundant = bearish)
- Year-over-year changes
- USDA estimate revisions (surprises move markets)

**Scripts**:
- `etl/wasde_corn_usda.py`
- `etl/wasde_soybean_usda.py`

**Example Usage**:
```bash
python etl/wasde_corn_usda.py
# Outputs: data/wasde_corn.csv (12 KB, ~252 rows)
```

**Trading Insight**:
- **Stocks-to-use < 10%**: Extremely tight supply (bullish)
- **Stocks-to-use > 20%**: Abundant supply (bearish)
- **Unexpected revisions**: Major price moves on report days

---

## 5. USDA Crop Conditions (Quality)

**What**: Weekly crop condition ratings from USDA NASS

**Source**: USDA National Agricultural Statistics Service (NASS)

**Coverage**: 2005-present (~1,040 weekly reports, seasonal May-November)

**Update Frequency**: Weekly (released Monday afternoons during growing season)

**Data Included**:
- **Condition ratings**: Very Poor, Poor, Fair, Good, Excellent
- **Crop progress**: % Planted, % Emerged, % Silking, % Mature, % Harvested
- **State-by-state**: Major producing states (IA, IL, IN, NE, MN, OH)

**Features Generated**: 10
- **Condition index**: % Good + Excellent (key metric)
- Year-over-year comparisons
- State-weighted averages
- Progress vs. 5-year average

**Scripts**:
- `etl/crop_conditions_nass.py` (corn)
- `etl/crop_conditions_soybean_nass.py`

**Example Usage**:
```bash
python etl/crop_conditions_nass.py
# Outputs: data/crop_conditions.csv (39 KB, ~1,040 rows)
```

**Trading Insight**:
- **Condition index < 50%**: Poor crop quality (bullish)
- **Condition index > 70%**: Excellent crop (bearish)
- **Critical periods**: July (pollination), August (grain fill)

---

## 6. Weather Data (Yield Impact)

**What**: Daily temperature, precipitation, and growing degree days (GDD)

**Source**: Open-Meteo Historical Weather API ([https://open-meteo.com/](https://open-meteo.com/))

**Coverage**: 2005-present (~7,300 daily observations)

**Update Lag**: **2-day lag** (data available 2 days after observation)

**Why Not NOAA**: NOAA Climate Data has 2-6 month publication lag, unsuitable for real-time trading.

**Data Included**:
- **Temperature**: Daily min, max, average (°F)
- **Precipitation**: Daily rainfall (inches)
- **Growing Degree Days (GDD)**: Accumulated heat units
- **Production-weighted indices**: Weighted by state production shares

**Features Generated**: 40
- GDD accumulation and anomalies
- Precipitation anomalies
- Drought indicators (consecutive dry days)
- Heat stress metrics (days > 95°F during pollination)

**Scripts**:
- `etl/weather_openmeteo.py` (supports --corn-only, --soy-only)

**Example Usage**:
```bash
python etl/weather_openmeteo.py --corn-only
# Outputs: data/weather_corn_belt_index.csv (1.2 MB, ~7,300 rows)
```

**Trading Insight**:
- **GDD deficit > 10% during pollination**: Yield damage risk (bullish)
- **Drought during grain fill**: Reduced yield (bullish)
- **Excessive rain during planting**: Delayed planting (bullish)

---

## Data Merging Process

All data sources are merged into a single dataset using **left join** on date:

```
corn_prices.csv (daily)                    [5,250 rows]
  LEFT JOIN cot_corn.csv (weekly)          [forward-filled]
  LEFT JOIN cftc_options_corn.csv (weekly) [forward-filled]
  LEFT JOIN wasde_corn.csv (monthly)       [forward-filled]
  LEFT JOIN crop_conditions.csv (weekly)   [forward-filled]
  LEFT JOIN weather_corn_belt_index.csv    [daily]
= corn_combined.csv (77 columns, 5,250 rows)
```

**Scripts**:
- `etl/merge_corn.py`
- `etl/merge_soybean.py`

**Output**:
- `data/corn_combined.csv` (3.2 MB, 77 columns)
- `data/soybean_combined.csv` (3.1 MB, 77 columns)

---

## Feature Engineering

From the 77 base columns, **180 engineered features** are created:

### Technical Indicators (30 features)
- Moving averages: 5, 10, 20, 50, 100, 200-day
- Momentum: RSI, MACD, ROC
- Volatility: Bollinger Bands, ATR
- Volume indicators

### Sentiment Features (25 features)
- COT percentile ranks (52-week rolling)
- Put/call ratio extremes
- Positioning divergences

### Fundamental Features (15 features)
- Stocks-to-use ratios
- USDA revision surprises
- Production estimates

### Weather Features (40 features)
- GDD accumulation and anomalies
- Precipitation anomalies
- Drought indices
- Heat stress metrics

### Seasonality Features (15 features)
- Day of year effects
- Month effects
- Growing season phase indicators

### Lag Features (55 features)
- 1, 3, 5, 10, 20-day lags of key features
- Trailing returns

**Scripts**:
- `features/corn_features.py`
- `features/soybean_features.py`

**Output**:
- `data/corn_combined_features.csv` (8.6 MB, 180 columns)
- `data/soybean_combined_features.csv` (8.6 MB, 180 columns)

---

## Data Update Schedule

| Data Source | Frequency | Release Time | Update Script |
|-------------|-----------|--------------|---------------|
| **Prices** | Daily | 4 PM ET (market close) | `etl/*_prices_yahoo.py` |
| **Weather** | Daily (2-day lag) | Continuous | `etl/weather_openmeteo.py` |
| **Crop Conditions** | Weekly | Monday PM | `etl/crop_conditions_*.py` |
| **COT / Options** | Weekly | Friday 3:30 PM ET | `etl/cot_*.py`, `etl/cftc_options_*.py` |
| **WASDE** | Monthly | 2nd Friday 12 PM ET | `etl/wasde_*.py` |

**Recommended Daily Update Time**: After market close (~5 PM ET or later)

---

## Data Quality Checks

The `scripts/verify_data.py` script checks:
- Latest data date (warns if > 5 days old)
- Missing values (flags if > 20% missing in key columns)
- Data continuity (checks for gaps)
- Price sanity checks (flags extreme moves)

**Usage**:
```bash
python scripts/verify_data.py
```

---

## API Keys (Optional)

Most data sources are **free and don't require API keys**. However, for enhanced access:

### NOAA Climate Data (Historical Weather)
- **When needed**: Initial historical data collection (2005-2015)
- **Get token**: [https://www.ncdc.noaa.gov/cdo-web/token](https://www.ncdc.noaa.gov/cdo-web/token)
- **Note**: Not used in production due to multi-month lag

### USDA NASS QuickStats (Crop Data)
- **When needed**: Some crop progress data scripts
- **Get key**: [https://quickstats.nass.usda.gov/api](https://quickstats.nass.usda.gov/api)
- **Note**: Most scripts scrape HTML, no key needed

Configure in `.env`:
```bash
NOAA_API_TOKEN=your_token_here
USDA_NASS_API_KEY=your_key_here
```

---

## Summary

| Data Source | Features | Coverage | Update | Importance |
|-------------|----------|----------|--------|------------|
| **Yahoo Finance** | 6 | Daily (20yr) | Daily | Critical |
| **CFTC COT** | 20 | Weekly (12yr) | Weekly | High |
| **CFTC Options** | 12 | Weekly (8yr) | Weekly | Medium |
| **USDA WASDE** | 15 | Monthly (20yr) | Monthly | High |
| **Crop Conditions** | 10 | Weekly (20yr) | Weekly | High |
| **Weather** | 40 | Daily (20yr) | Daily (2-day lag) | High |
| **Features** | 180 | Derived | Daily | Critical |

**Total Raw Data Size**: ~27 MB
**Total Features**: 180 columns
**Total Observations**: ~5,250 daily rows

---

For usage examples, see [QUICKSTART.md](QUICKSTART.md).
