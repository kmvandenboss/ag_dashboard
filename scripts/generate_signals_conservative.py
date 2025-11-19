#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Signals Generator - Conservative v2.0 Model (15% R)

Conservative model for capital preservation and lower risk.

Usage:
    python scripts/generate_signals_conservative.py [--save-csv]
"""

import pandas as pd
import numpy as np
import json
import joblib
import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import warnings
warnings.filterwarnings('ignore')

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / 'data' / 'corn_combined_features.csv'
CONFIG_PATH = BASE_DIR / 'models' / 'conservative_v2.0' / 'model_config.json'
MODEL_DIR = BASE_DIR / 'models' / 'conservative_v2.0'
SIGNALS_DIR = BASE_DIR / 'signals'
SIGNALS_DIR.mkdir(exist_ok=True)

# Load configuration
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Extract parameters
LONG_PERCENTILE = config['parameters']['thresholds']['long_percentile']  # 0.87
SHORT_PERCENTILE = config['parameters']['thresholds']['short_percentile']  # 0.13
ROLLING_WINDOW = config['parameters']['thresholds']['rolling_window']
R_PER_TRADE = config['parameters']['position_sizing']['r_per_trade']  # 0.15
ATR_MULTIPLIER = config['parameters']['stops']['atr_multiplier']  # 3.25
ATR_PERIOD = config['parameters']['stops']['atr_period']
PROFIT_TARGET_R = config['parameters']['profit_targets']['target_r']  # 1.75
TIME_STOP_DAYS = config['parameters']['stops']['time_stop_days']


def load_data():
    """Load latest data"""
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


def get_feature_columns(df):
    """Get feature columns"""
    exclude_cols = ['date', 'fwd_ret_5d', 'fwd_ret_10d', 'fwd_ret_20d',
                    'target_up_5d', 'target_up_10d', 'target_up_20d',
                    'regime_hmm', 'regime_name', 'regime_predicted',
                    'open_interest', 'notes', 'prcp_anomaly', 'tavg_anomaly']

    feature_cols = [col for col in df.columns if col not in exclude_cols]
    missing_pct = df[feature_cols].isna().mean()
    feature_cols = [col for col in feature_cols if missing_pct[col] < 0.8]

    return feature_cols


def calculate_atr(prices, high=None, low=None, period=20):
    """Calculate Average True Range"""
    if high is not None and low is not None:
        tr1 = high - low
        tr2 = abs(high - prices.shift(1))
        tr3 = abs(low - prices.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    else:
        # Estimate from close prices
        tr = prices.pct_change().abs().rolling(5).std() * prices

    atr = tr.rolling(period).mean()
    return atr


def load_model():
    """Load model artifacts"""
    model = joblib.load(MODEL_DIR / 'model.pkl')
    imputer = joblib.load(MODEL_DIR / 'imputer.pkl')
    scaler = joblib.load(MODEL_DIR / 'scaler.pkl')
    return model, imputer, scaler


def generate_signals(df, model, imputer, scaler, feature_cols):
    """Generate trading signals for latest data"""

    # Get latest 120 days (need rolling window + buffer)
    recent_df = df.tail(150).copy()

    # Prepare features
    features = recent_df[feature_cols].ffill()
    features_imputed = imputer.transform(features)
    features_scaled = scaler.transform(features_imputed)

    # Predict
    predictions = model.predict(features_scaled)
    recent_df['prediction'] = predictions

    # Calculate percentiles (rolling)
    recent_df['pred_percentile'] = recent_df['prediction'].rolling(
        ROLLING_WINDOW, min_periods=20
    ).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

    # Calculate ATR
    if 'high' in recent_df.columns and 'low' in recent_df.columns:
        recent_df['atr'] = calculate_atr(
            recent_df['close'],
            recent_df['high'],
            recent_df['low'],
            period=ATR_PERIOD
        )
    else:
        recent_df['atr'] = calculate_atr(recent_df['close'], period=ATR_PERIOD)

    # Get today's data (most recent row with valid percentile)
    today = recent_df[recent_df['pred_percentile'].notna()].iloc[-1]

    # Determine signal (Conservative: 87th/13th percentile, MORE selective)
    signal = None
    position_size = 0
    percentile = today['pred_percentile']

    if percentile >= LONG_PERCENTILE:  # 0.87
        signal = 'LONG'
        # Conviction-based sizing: ≥92nd (1.0×), 87-92nd (0.75×)
        if percentile >= 0.92:
            position_size = 1.0
        else:  # 0.87-0.92
            position_size = 0.75

    elif percentile <= SHORT_PERCENTILE:  # 0.13
        signal = 'SHORT'
        # Conviction-based sizing
        if percentile <= 0.08:
            position_size = 1.0
        else:  # 0.08-0.13
            position_size = 0.75

    # Calculate stop loss and targets if we have a signal
    if signal:
        current_price = today['close']
        atr = today['atr']
        stop_distance = ATR_MULTIPLIER * atr

        if signal == 'LONG':
            stop_loss = current_price - stop_distance
            profit_target = current_price + (PROFIT_TARGET_R * stop_distance)
        else:  # SHORT
            stop_loss = current_price + stop_distance
            profit_target = current_price - (PROFIT_TARGET_R * stop_distance)

        # Position size in R
        position_size_r = R_PER_TRADE * position_size

        return {
            'date': today['date'],
            'signal': signal,
            'confidence': percentile if signal == 'LONG' else (1 - percentile),
            'prediction': today['prediction'],
            'percentile': percentile,
            'current_price': current_price,
            'stop_loss': stop_loss,
            'profit_target': profit_target,
            'position_size_pct': position_size_r * 100,
            'atr': atr,
            'time_stop_date': today['date'] + timedelta(days=TIME_STOP_DAYS)
        }
    else:
        return {
            'date': today['date'],
            'signal': 'HOLD',
            'confidence': 0,
            'prediction': today['prediction'],
            'percentile': percentile,
            'current_price': today['close'],
            'stop_loss': None,
            'profit_target': None,
            'position_size_pct': 0,
            'atr': today['atr'],
            'time_stop_date': None
        }


def format_signal_output(signal):
    """Format signal for display"""

    output = []
    output.append("=" * 80)
    output.append("CORN FUTURES - CONSERVATIVE v2.0 SIGNAL")
    output.append("=" * 80)
    output.append(f"Date: {signal['date'].strftime('%Y-%m-%d')}")
    output.append(f"Model: Conservative v2.0 (15% R)")
    output.append("")

    if signal['signal'] == 'HOLD':
        output.append("Signal: HOLD (No trade)")
        output.append(f"   Current Price: ${signal['current_price']:.2f}")
        output.append(f"   Prediction: {signal['prediction']:+.2%}")
        output.append(f"   Percentile: {signal['percentile']:.1%} (need >{LONG_PERCENTILE:.0%} or <{SHORT_PERCENTILE:.0%})")
        output.append("")
        output.append("No action required - waiting for stronger signal")

    else:
        emoji = "[LONG]" if signal['signal'] == 'LONG' else "[SHORT]"
        output.append(f"{emoji} Signal: {signal['signal']}")
        output.append(f"   Confidence: {signal['confidence']:.1%} (Percentile: {signal['percentile']:.1%})")
        output.append("")
        output.append("Entry:")
        output.append(f"   Price: ${signal['current_price']:.2f}")
        output.append(f"   Position Size: {signal['position_size_pct']:.1f}% of equity")
        output.append("")
        output.append("Risk Management:")
        output.append(f"   Stop Loss: ${signal['stop_loss']:.2f} ({abs(signal['current_price'] - signal['stop_loss']) / signal['current_price']:.2%})")
        output.append(f"   Profit Target: ${signal['profit_target']:.2f} ({abs(signal['profit_target'] - signal['current_price']) / signal['current_price']:.2%})")
        output.append(f"   Risk/Reward: 1:{PROFIT_TARGET_R}")
        output.append(f"   Time Stop: {signal['time_stop_date'].strftime('%Y-%m-%d')} ({TIME_STOP_DAYS} days)")
        output.append("")
        output.append("Technical:")
        output.append(f"   Predicted Return: {signal['prediction']:+.2%} (10-day)")
        output.append(f"   ATR (20-day): ${signal['atr']:.2f}")

    output.append("")
    output.append("=" * 80)
    output.append("This is a signal, not financial advice. Trade at your own risk.")
    output.append("=" * 80)

    return "\n".join(output)


def save_signal_history(signal):
    """Save signal to CSV history"""

    history_file = SIGNALS_DIR / 'signal_history_conservative.csv'

    # Create DataFrame for this signal
    signal_df = pd.DataFrame([{
        'date': signal['date'],
        'signal': signal['signal'],
        'confidence': signal['confidence'],
        'prediction': signal['prediction'],
        'percentile': signal['percentile'],
        'current_price': signal['current_price'],
        'stop_loss': signal['stop_loss'],
        'profit_target': signal['profit_target'],
        'position_size_pct': signal['position_size_pct'],
        'atr': signal['atr'],
        'time_stop_date': signal['time_stop_date']
    }])

    # Append to history
    if history_file.exists():
        history = pd.read_csv(history_file)
        history = pd.concat([history, signal_df], ignore_index=True)
    else:
        history = signal_df

    history.to_csv(history_file, index=False)
    print(f"Signal saved to {history_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate daily trading signals - Conservative v2.0')
    parser.add_argument('--save-csv', action='store_true', help='Save signal to CSV history')
    args = parser.parse_args()

    print("Corn Futures - Conservative v2.0 Signal Generator")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    print("Loading data...")
    df = load_data()
    print(f"[OK] Loaded {len(df)} rows (latest: {df['date'].max().strftime('%Y-%m-%d')})")

    # Get features
    feature_cols = get_feature_columns(df)
    print(f"[OK] Using {len(feature_cols)} features")

    # Load model
    model, imputer, scaler = load_model()
    print(f"[OK] Model loaded")

    # Generate signals
    print("\nGenerating signals...")
    signal = generate_signals(df, model, imputer, scaler, feature_cols)

    # Display signal
    print("\n" + format_signal_output(signal))

    # Save to CSV if requested
    if args.save_csv:
        save_signal_history(signal)

    print(f"\n[OK] Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
