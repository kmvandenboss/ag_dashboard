#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Signals Generator - High Conviction Model (20% R, 90th/10th percentile)

This script generates daily BUY/SELL/SHORT signals for both corn and soybean futures
based on the validated High Conviction Model. It should be run daily after market close.

Usage:
    python generate_signals_high_conviction.py [--email] [--telegram] [--save-csv] [--commodity corn|soybean|both]

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

# Base directory
BASE_DIR = Path(__file__).parent.parent
SIGNALS_DIR = BASE_DIR / 'signals'
SIGNALS_DIR.mkdir(exist_ok=True)

# Commodity configurations for High Conviction models
COMMODITY_CONFIGS = {
    'corn': {
        'data_path': BASE_DIR / 'data' / 'corn_combined_features.csv',
        'config_path': BASE_DIR / 'models' / 'corn_high_conviction' / 'model_config.json',
        'model_dir': BASE_DIR / 'models' / 'corn_high_conviction',
        'display_name': 'Corn',
        'emoji': '🌽'
    },
    'soybean': {
        'data_path': BASE_DIR / 'data' / 'soybean_combined_features.csv',
        'config_path': BASE_DIR / 'models' / 'soy_high_conviction' / 'model_config.json',
        'model_dir': BASE_DIR / 'models' / 'soy_high_conviction',
        'display_name': 'Soybeans',
        'emoji': '🫘'
    }
}


def load_data(data_path):
    """Load latest data"""
    df = pd.read_csv(data_path)
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


def load_model(model_dir):
    """Load existing model (high conviction models use _2024 suffix)"""

    # Try _2024 suffix first (high conviction models)
    model_path = model_dir / 'model_2024.pkl'
    scaler_path = model_dir / 'scaler_2024.pkl'
    imputer_path = model_dir / 'imputer_2024.pkl'

    if not model_path.exists():
        # Fallback to standard naming
        model_path = model_dir / 'model.pkl'
        scaler_path = model_dir / 'scaler.pkl'
        imputer_path = model_dir / 'imputer.pkl'

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found in {model_dir}. Please train the model first.")

    print(f"Loading model from {model_path}")
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    imputer = joblib.load(imputer_path)

    # Get feature names from imputer (most reliable source)
    feature_names = None
    if hasattr(imputer, 'feature_names_in_'):
        feature_names = list(imputer.feature_names_in_)
        print(f"✅ Loaded {len(feature_names)} feature names from imputer")
    else:
        print("⚠️  Could not get feature names from imputer")

    return model, imputer, scaler, feature_names


def generate_signals(df, model, imputer, scaler, feature_cols, config):
    """Generate trading signals for latest data"""

    # Extract parameters from config
    LONG_PERCENTILE = config['parameters']['thresholds']['long_percentile']
    SHORT_PERCENTILE = config['parameters']['thresholds']['short_percentile']
    ROLLING_WINDOW = config['parameters']['thresholds']['rolling_window']
    R_PER_TRADE = config['parameters']['position_sizing']['r_per_trade']
    ATR_MULTIPLIER = config['parameters']['stops']['atr_multiplier']
    ATR_PERIOD = config['parameters']['stops']['atr_period']
    PROFIT_TARGET_R = config['parameters']['profit_targets']['target_r']
    TIME_STOP_DAYS = config['parameters']['stops']['time_stop_days']

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
        # High conviction = full size
        position_size = 1.0

    elif percentile <= SHORT_PERCENTILE:
        signal = 'SHORT'
        # High conviction = full size
        position_size = 1.0

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
            'time_stop_date': today['date'] + timedelta(days=TIME_STOP_DAYS),
            'config': config  # Include config for formatting
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
            'time_stop_date': None,
            'config': config  # Include config for formatting
        }


def format_signal_output(signal, commodity_name, emoji):
    """Format signal for display"""

    config = signal['config']
    LONG_PERCENTILE = config['parameters']['thresholds']['long_percentile']
    SHORT_PERCENTILE = config['parameters']['thresholds']['short_percentile']
    PROFIT_TARGET_R = config['parameters']['profit_targets']['target_r']
    TIME_STOP_DAYS = config['parameters']['stops']['time_stop_days']

    output = []
    output.append("=" * 80)
    output.append(f"{emoji} {commodity_name.upper()} FUTURES - HIGH CONVICTION SIGNAL")
    output.append("=" * 80)
    output.append(f"Date: {signal['date'].strftime('%Y-%m-%d')}")
    output.append(f"Model: High Conviction (90th/10th percentile)")
    output.append("")

    if signal['signal'] == 'HOLD':
        output.append("📊 Signal: HOLD (No trade)")
        output.append(f"   Current Price: ${signal['current_price']:.2f}")
        output.append(f"   Prediction: {signal['prediction']:+.2%}")
        output.append(f"   Percentile: {signal['percentile']:.1%} (need >{LONG_PERCENTILE:.0%} or <{SHORT_PERCENTILE:.0%})")
        output.append("")
        output.append("✋ No action required - waiting for HIGH CONVICTION signal (top/bottom 10%)")

    else:
        emoji_signal = "🟢" if signal['signal'] == 'LONG' else "🔴"
        output.append(f"{emoji_signal} Signal: {signal['signal']} ⚡ HIGH CONVICTION")
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


def save_signal_history(signal, commodity):
    """Save signal to CSV history"""

    history_file = SIGNALS_DIR / f'signal_history_high_conviction_{commodity}.csv'

    # Create DataFrame for this signal
    signal_df = pd.DataFrame([{
        'date': signal['date'],
        'commodity': commodity,
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


def process_commodity(commodity, commodity_config, args):
    """Process signals for a single commodity"""

    print("\n" + "=" * 80)
    print(f"{commodity_config['emoji']} Processing {commodity_config['display_name']} (High Conviction)...")
    print("=" * 80)

    # Load configuration
    with open(commodity_config['config_path'], 'r') as f:
        config = json.load(f)

    # Load data
    print("Loading data...")
    df = load_data(commodity_config['data_path'])
    print(f"✅ Loaded {len(df)} rows (latest: {df['date'].max().strftime('%Y-%m-%d')})")

    # Load model (get feature names from saved model)
    model, imputer, scaler, feature_names = load_model(commodity_config['model_dir'])

    # Use saved feature names if available, otherwise get from data
    if feature_names:
        feature_cols = feature_names
        print(f"✅ Using {len(feature_cols)} features from model")
    else:
        feature_cols = get_feature_columns(df)
        print(f"✅ Using {len(feature_cols)} features from data")

    # Generate signals
    print("\nGenerating signals...")
    signal = generate_signals(df, model, imputer, scaler, feature_cols, config)

    # Display signal
    print("\n" + format_signal_output(signal, commodity_config['display_name'], commodity_config['emoji']))

    # Save to CSV if requested
    if args.save_csv:
        save_signal_history(signal, commodity)

    # Send alerts if requested
    if args.email:
        send_email_alert(signal, args.email)

    if args.telegram:
        send_telegram_alert(signal, args.telegram)

    return signal


def main():
    parser = argparse.ArgumentParser(description='Generate HIGH CONVICTION signals for corn and soybean futures')
    parser.add_argument('--email', type=str, help='Email address for alerts')
    parser.add_argument('--telegram', type=str, help='Telegram chat ID for alerts')
    parser.add_argument('--save-csv', action='store_true', help='Save signal to CSV history')
    parser.add_argument('--commodity', type=str, choices=['corn', 'soybean', 'both'], default='both',
                        help='Which commodity to generate signals for (default: both)')
    args = parser.parse_args()

    print("⚡ High Conviction Signal Generator (90th/10th percentile)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Determine which commodities to process
    commodities_to_process = []
    if args.commodity == 'both':
        commodities_to_process = ['corn', 'soybean']
    else:
        commodities_to_process = [args.commodity]

    # Process each commodity
    results = {}
    for commodity in commodities_to_process:
        try:
            signal = process_commodity(commodity, COMMODITY_CONFIGS[commodity], args)
            results[commodity] = signal
        except Exception as e:
            print(f"\n❌ Error processing {commodity}: {e}")
            import traceback
            traceback.print_exc()
            results[commodity] = None

    # Summary
    print("\n" + "=" * 80)
    print("HIGH CONVICTION SUMMARY")
    print("=" * 80)
    for commodity, signal in results.items():
        if signal:
            emoji = COMMODITY_CONFIGS[commodity]['emoji']
            signal_type = signal['signal']
            if signal_type != 'HOLD':
                signal_emoji = "⚡🟢" if signal_type == 'LONG' else "⚡🔴"
                print(f"{emoji} {commodity.capitalize():10s}: {signal_emoji} {signal_type} (HIGH CONVICTION)")
            else:
                signal_emoji = "⚪"
                print(f"{emoji} {commodity.capitalize():10s}: {signal_emoji} {signal_type}")
        else:
            print(f"❌ {commodity.capitalize():10s}: FAILED")

    print(f"\n✅ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
