# AG Futures Signals Dashboard

Terminal-style Streamlit dashboard for displaying High Conviction corn and soybean trading signals.

## Features

- **Most Recent Signal**: Display of the last completed trade from backtest
- **YTD Performance**: 2024-2025 walk-forward backtest results with key metrics
- **Trade History**: Complete YTD trade log with PnL in R-multiples
- **All Periods Summary**: Historical validation across 6 periods (2014-2025)
- **Aggregate Statistics**: Overall performance metrics across all validation periods

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

### 3. View Dashboard

- Select either CORN or SOYBEANS from the dropdown
- View most recent completed trade
- Review YTD 2024-2025 performance metrics
- Examine complete trade history
- Analyze performance across all validation periods

## Terminal Style

The dashboard features a retro terminal aesthetic:
- Dark background (#0a0a0a)
- Green text (#00ff00)
- Monospace font (Courier New)
- ASCII box drawing

## Data Sources

All data is loaded from walk-forward validation results (included in repository):
- `models/corn_high_conviction/validation_results/walk_forward_6period_results.csv`
- `models/corn_high_conviction/validation_results/walk_forward_6period_trades.csv`
- `models/soy_high_conviction/validation_results/walk_forward_6period_results.csv`
- `models/soy_high_conviction/validation_results/walk_forward_6period_trades.csv`

No raw data files or trained models are required - only the validation results.

## Model Configuration

- **Model Type**: High Conviction (90th/10th percentile)
- **Position Size**: 20% R per trade
- **Risk/Reward**: 1:2
- **Stop Loss**: 2x ATR(20)
- **Time Stop**: 10 days

## Notes

- Dashboard displays **historical backtest data only** (not live trading signals)
- The most recent signal shown is the last completed trade from the 2024-2025 validation period
- All performance metrics are based on walk-forward validation (2014-2025)
- YTD refers to the 2024-2025 validation period
- Data is cached for performance

## Deploying to Streamlit Cloud (Optional)

1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect your repository
4. Select `ag_dashboard/streamlit_dashboard.py`
5. Deploy

**Disclaimer**: This dashboard displays trading signals for informational purposes only. Not financial advice.
