# Daily Signal Update Workflow

This document explains how to update trading signals for the cloud dashboard.

## Overview

The dashboard displays signals from `signals/current_signals.csv` which is tracked in git. Every morning, you'll generate new signals locally and push them to GitHub, which automatically updates the Streamlit Cloud dashboard.

## Daily Workflow

### Option 1: Using the Update Script (Recommended)

**Windows:**
```bash
cd ag_dashboard
update_signals.bat
```

**Mac/Linux:**
```bash
cd ag_dashboard
chmod +x update_signals.sh
./update_signals.sh
```

The script will:
1. Generate current signals for corn and soybeans
2. Save to `signals/current_signals.csv`
3. Commit the file to git
4. Push to GitHub
5. Cloud dashboard updates automatically (within ~1 minute)

### Option 2: Manual Steps

```bash
cd ag_dashboard

# Generate signals
python scripts/generate_signals_high_conviction.py

# Push to GitHub
git add signals/current_signals.csv
git commit -m "Update signals for 2025-11-21"
git push origin main
```

## Signal Priority

The dashboard uses a three-tier fallback system:

1. **Saved Signals** (Priority 1) - Loads from `signals/current_signals.csv`
   - Used by cloud deployment
   - Updated via daily workflow above

2. **Live Generation** (Priority 2) - Generates from local data files
   - Used when running locally with data files
   - Requires `data/` and `models/` directories

3. **Historical Data** (Priority 3) - Shows last backtest trade
   - Fallback when no saved signals or data files
   - Always available from validation results

## Signal File Format

`signals/current_signals.csv` contains:
- `date` - Signal generation date
- `commodity` - corn or soybean
- `signal` - LONG, SHORT, or HOLD
- `confidence` - Percentile-based confidence (0-1)
- `current_price` - Entry price
- `stop_loss` - Stop loss level
- `profit_target` - Profit target level
- `position_size_pct` - Position size (% of equity)
- `atr` - Current ATR value
- `time_stop_date` - Time-based exit date

## Automation (Optional)

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 10:00 AM (after market open)
4. Action: Start a program
5. Program: `C:\path\to\ag_dashboard\update_signals.bat`

### Mac/Linux Cron
```bash
# Edit crontab
crontab -e

# Add line (runs daily at 10:00 AM)
0 10 * * * cd /path/to/ag_dashboard && ./update_signals.sh
```

## Troubleshooting

### Signals not showing on cloud
1. Check if `signals/current_signals.csv` exists in GitHub repo
2. Verify the file has today's date
3. Wait 1-2 minutes for Streamlit Cloud to redeploy
4. Try clearing cache: Settings → Clear cache in dashboard

### Git push fails
```bash
# Pull latest changes first
git pull origin main

# Then push
git push origin main
```

### Signal generation fails
- Ensure you're in the `ag_dashboard` directory
- Check that data files are up to date
- Verify model files exist in `models/` directories

## Notes

- The cloud dashboard caches signals for 5 minutes for performance
- Signals are timezone-aware (your local timezone)
- Old signals are kept in git history for tracking
- The signal generator always processes both corn and soybeans
