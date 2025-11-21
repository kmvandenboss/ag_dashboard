# AG Futures Signals Dashboard

Terminal-style Streamlit dashboard for displaying High Conviction corn and soybean trading signals.

## Features

- **Current Signals**: Real-time LONG/SHORT/HOLD signals with entry, stop, and target prices
- **YTD Performance**: 2024-2025 walk-forward backtest results
- **Trade History**: Complete YTD trade log with PnL
- **All Periods Summary**: Historical validation across 6 periods (2014-2025)

## Quick Start

### 1. Install Dependencies

```bash
cd ag_dashboard
pip install -r requirements.txt
```

### 2. Run Dashboard

```bash
streamlit run streamlit_dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

### 3. View Signals

- Select either CORN or SOYBEANS from the dropdown
- View current signal status (LONG/SHORT/HOLD)
- Review YTD performance metrics
- Examine complete trade history

## Terminal Style

The dashboard features a retro terminal aesthetic:
- Dark background (#0a0a0a)
- Green text (#00ff00)
- Monospace font (Courier New)
- ASCII box drawing

## Data Sources

All data is loaded from the existing model validation results:
- `models/corn_high_conviction/validation_results/`
- `models/soy_high_conviction/validation_results/`

## Model Configuration

- **Model Type**: High Conviction (90th/10th percentile)
- **Position Size**: 20% R per trade
- **Risk/Reward**: 1:2
- **Stop Loss**: 2x ATR(20)
- **Time Stop**: 10 days

## Notes

- Signals are generated from the most recent data in the combined features files
- The dashboard uses cached data for performance
- All performance metrics are based on walk-forward validation (2014-2025)
- YTD refers to the 2024-2025 validation period

## Deploying to Streamlit Cloud (Optional)

1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect your repository
4. Select `ag_dashboard/streamlit_dashboard.py`
5. Deploy

**Disclaimer**: This dashboard displays trading signals for informational purposes only. Not financial advice.
