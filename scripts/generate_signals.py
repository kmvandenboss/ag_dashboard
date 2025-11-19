#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Signals Generator - Moderate Model (20% R)

This script generates daily BUY/SELL/SHORT signals for corn futures based on the
validated Moderate Model. It should be run daily after market close.

Usage:
    python generate_daily_signals.py [--email] [--telegram] [--save-csv]

Output:
    - Console output with today's signals
    - Optional: Email alert
    - Optional: Telegram notification
    - Optional: CSV file with signal history
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
CONFIG_PATH = BASE_DIR / 'models' / 'moderate' / 'model_config.json'
MODEL_DIR = BASE_DIR / 'models' / 'moderate'
SIGNALS_DIR = BASE_DIR / 'signals'
SIGNALS_DIR.mkdir(exist_ok=True)

# Load configuration
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Extract parameters
LONG_PERCENTILE = config['parameters']['thresholds']['long_percentile']
SHORT_PERCENTILE = config['parameters']['thresholds']['short_percentile']
ROLLING_WINDOW = config['parameters']['thresholds']['rolling_window']
R_PER_TRADE = config['parameters']['position_sizing']['r_per_trade']
ATR_MULTIPLIER = config['parameters']['stops']['atr_multiplier']
ATR_PERIOD = config['parameters']['stops']['atr_period']
PROFIT_TARGET_R = config['parameters']['profit_targets']['target_r']
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


def train_or_load_model(df, feature_cols):
    """Train new model or load existing one"""

    model_path = MODEL_DIR / 'model.pkl'
    scaler_path = MODEL_DIR / 'scaler.pkl'

    # Check if we should retrain (monthly or if model doesn't exist)
    retrain = False
    if not model_path.exists():
        retrain = True
        print("No existing model found - training new model...")
    else:
        # Check model age
        model_age_days = (datetime.now() - datetime.fromtimestamp(model_path.stat().st_mtime)).days
        if model_age_days > 30:
            retrain = True
            print(f"Model is {model_age_days} days old - retraining...")

    if retrain:
        # Train new model on all available data
        from xgboost import XGBRegressor
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import RobustScaler

        target_col = 'fwd_ret_10d'

        # Prepare data
        train_data = df[df[target_col].notna()].copy()

        # Prepare features
        train_features = train_data[feature_cols].ffill()
        imputer = SimpleImputer(strategy='median')
        train_features_imputed = imputer.fit_transform(train_features)

        # Scale features
        scaler = RobustScaler()
        train_features_scaled = scaler.fit_transform(train_features_imputed)

        feature_names = imputer.get_feature_names_out(input_features=feature_cols)
        X_train = pd.DataFrame(train_features_scaled, columns=feature_names)
        y_train = train_data[target_col].values

        # Train model
        print(f"Training on {len(X_train)} samples...")
        model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        model.fit(X_train, y_train, verbose=False)

        # Save model and scaler
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(imputer, MODEL_DIR / 'imputer.pkl')

        print(f"✅ Model trained and saved to {model_path}")

    else:
        # Load existing model
        print(f"Loading existing model from {model_path}")
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        imputer = joblib.load(MODEL_DIR / 'imputer.pkl')

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

    # Determine signal
    signal = None
    position_size = 0
    percentile = today['pred_percentile']

    if percentile >= LONG_PERCENTILE:
        signal = 'LONG'
        # Conviction-based sizing
        if percentile >= 0.90:
            position_size = 1.0
        elif percentile >= 0.85:
            position_size = 0.75
        else:
            position_size = 0.5

    elif percentile <= SHORT_PERCENTILE:
        signal = 'SHORT'
        # Conviction-based sizing
        if percentile <= 0.10:
            position_size = 1.0
        elif percentile <= 0.15:
            position_size = 0.75
        else:
            position_size = 0.20

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
    output.append("🌽 CORN FUTURES - DAILY SIGNAL")
    output.append("=" * 80)
    output.append(f"Date: {signal['date'].strftime('%Y-%m-%d')}")
    output.append(f"Model: Moderate (20% R)")
    output.append("")

    if signal['signal'] == 'HOLD':
        output.append("📊 Signal: HOLD (No trade)")
        output.append(f"   Current Price: ${signal['current_price']:.2f}")
        output.append(f"   Prediction: {signal['prediction']:+.2%}")
        output.append(f"   Percentile: {signal['percentile']:.1%} (need >{LONG_PERCENTILE:.0%} or <{SHORT_PERCENTILE:.0%})")
        output.append("")
        output.append("✋ No action required - waiting for stronger signal")

    else:
        emoji = "🟢" if signal['signal'] == 'LONG' else "🔴"
        output.append(f"{emoji} Signal: {signal['signal']}")
        output.append(f"   Confidence: {signal['confidence']:.1%} (Percentile: {signal['percentile']:.1%})")
        output.append("")
        output.append("📈 Entry:")
        output.append(f"   Price: ${signal['current_price']:.2f}")
        output.append(f"   Position Size: {signal['position_size_pct']:.1f}% of equity")
        output.append("")
        output.append("🎯 Risk Management:")
        output.append(f"   Stop Loss: ${signal['stop_loss']:.2f} ({abs(signal['current_price'] - signal['stop_loss']) / signal['current_price']:.2%})")
        output.append(f"   Profit Target: ${signal['profit_target']:.2f} ({abs(signal['profit_target'] - signal['current_price']) / signal['current_price']:.2%})")
        output.append(f"   Risk/Reward: 1:{PROFIT_TARGET_R}")
        output.append(f"   Time Stop: {signal['time_stop_date'].strftime('%Y-%m-%d')} ({TIME_STOP_DAYS} days)")
        output.append("")
        output.append("📊 Technical:")
        output.append(f"   Predicted Return: {signal['prediction']:+.2%} (10-day)")
        output.append(f"   ATR (20-day): ${signal['atr']:.2f}")

    output.append("")
    output.append("=" * 80)
    output.append("⚠️  This is a signal, not financial advice. Trade at your own risk.")
    output.append("=" * 80)

    return "\n".join(output)


def save_signal_history(signal):
    """Save signal to CSV history"""

    history_file = SIGNALS_DIR / 'signal_history.csv'

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
    print(f"✅ Signal saved to {history_file}")


def send_email_alert(signal, to_email):
    """Send email alert (placeholder - implement with your email service)"""
    print(f"📧 Email alert would be sent to {to_email}")
    # TODO: Implement email sending
    # Example using smtplib or SendGrid/Mailgun API


def send_telegram_alert(signal, chat_id):
    """Send Telegram alert (placeholder - implement with Telegram Bot API)"""
    print(f"📱 Telegram alert would be sent to chat {chat_id}")
    # TODO: Implement Telegram bot
    # Example using python-telegram-bot library


def main():
    parser = argparse.ArgumentParser(description='Generate daily trading signals')
    parser.add_argument('--email', type=str, help='Email address for alerts')
    parser.add_argument('--telegram', type=str, help='Telegram chat ID for alerts')
    parser.add_argument('--save-csv', action='store_true', help='Save signal to CSV history')
    args = parser.parse_args()

    print("🌽 Corn Futures - Daily Signal Generator")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    print("Loading data...")
    df = load_data()
    print(f"✅ Loaded {len(df)} rows (latest: {df['date'].max().strftime('%Y-%m-%d')})")

    # Get features
    feature_cols = get_feature_columns(df)
    print(f"✅ Using {len(feature_cols)} features")

    # Train or load model
    model, imputer, scaler = train_or_load_model(df, feature_cols)

    # Generate signals
    print("\nGenerating signals...")
    signal = generate_signals(df, model, imputer, scaler, feature_cols)

    # Display signal
    print("\n" + format_signal_output(signal))

    # Save to CSV if requested
    if args.save_csv:
        save_signal_history(signal)

    # Send alerts if requested
    if args.email:
        send_email_alert(signal, args.email)

    if args.telegram:
        send_telegram_alert(signal, args.telegram)

    print(f"\n✅ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
