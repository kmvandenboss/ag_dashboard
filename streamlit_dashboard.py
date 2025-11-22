#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AG Futures Signals Dashboard - Terminal Style
High Conviction Corn & Soybean Trading Signals

A minimal, terminal-style dashboard for displaying trading signals
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import os

# Page configuration - terminal style
st.set_page_config(
    page_title="AG SIGNALS | Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Terminal-style CSS
st.markdown("""
    <style>
    /* Dark terminal background */
    .stApp {
        background-color: #0a0a0a;
        color: #00ff00;
        font-family: 'Courier New', monospace;
    }

    /* Headers */
    h1, h2, h3 {
        color: #00ff00;
        font-family: 'Courier New', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #00ff00;
        font-family: 'Courier New', monospace;
        font-size: 28px;
    }

    [data-testid="stMetricLabel"] {
        color: #00ff00;
        font-family: 'Courier New', monospace;
    }

    /* Dataframes */
    .dataframe {
        background-color: #0a0a0a !important;
        color: #00ff00 !important;
        font-family: 'Courier New', monospace !important;
        border: 1px solid #00ff00 !important;
    }

    .dataframe th {
        background-color: #0a0a0a !important;
        color: #00ff00 !important;
        border: 1px solid #00ff00 !important;
    }

    .dataframe td {
        background-color: #0a0a0a !important;
        color: #00ff00 !important;
        border: 1px solid #00ff00 !important;
    }

    /* Dividers */
    hr {
        border-color: #00ff00;
    }

    /* Text */
    p, div {
        color: #00ff00;
        font-family: 'Courier New', monospace;
    }

    /* Terminal box style - mobile responsive */
    .terminal-box {
        background-color: #0a0a0a;
        border: 2px solid #00ff00;
        padding: 15px;
        font-family: 'Courier New', monospace;
        color: #00ff00;
        white-space: pre-wrap;
        word-wrap: break-word;
        margin: 10px 0;
        overflow-x: hidden;
        max-width: 100%;
        font-size: clamp(10px, 2.5vw, 14px);
        line-height: 1.3;
    }

    /* Mobile optimization */
    @media (max-width: 768px) {
        .terminal-box {
            padding: 10px;
            font-size: 10px;
            line-height: 1.2;
        }

        h1 {
            font-size: 18px !important;
            letter-spacing: 1px !important;
        }

        h2, h3 {
            font-size: 14px !important;
            letter-spacing: 1px !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 18px !important;
        }
    }

    /* Prevent horizontal scroll */
    .main .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Base directory
BASE_DIR = Path(__file__).parent

# Commodity configurations
COMMODITY_CONFIGS = {
    'corn': {
        'data_path': BASE_DIR / 'data' / 'corn_combined_features.csv',
        'config_path': BASE_DIR / 'models' / 'corn_high_conviction' / 'model_config.json',
        'model_dir': BASE_DIR / 'models' / 'corn_high_conviction',
        'validation_results': BASE_DIR / 'models' / 'corn_high_conviction' / 'validation_results' / 'walk_forward_6period_results.csv',
        'validation_trades': BASE_DIR / 'models' / 'corn_high_conviction' / 'validation_results' / 'walk_forward_6period_trades.csv',
        'display_name': 'CORN',
        'emoji': '🌽'
    },
    'soybean': {
        'data_path': BASE_DIR / 'data' / 'soybean_combined_features.csv',
        'config_path': BASE_DIR / 'models' / 'soy_high_conviction' / 'model_config.json',
        'model_dir': BASE_DIR / 'models' / 'soy_high_conviction',
        'validation_results': BASE_DIR / 'models' / 'soy_high_conviction' / 'validation_results' / 'walk_forward_6period_results.csv',
        'validation_trades': BASE_DIR / 'models' / 'soy_high_conviction' / 'validation_results' / 'walk_forward_6period_trades.csv',
        'display_name': 'SOYBEANS',
        'emoji': '🫘'
    }
}


def check_live_data_available(config):
    """Check if live data files are available"""
    return config['data_path'].exists() and config['config_path'].exists()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_saved_signals():
    """Load saved signals from CSV file"""
    signals_file = BASE_DIR / 'signals' / 'current_signals.csv'

    if signals_file.exists():
        try:
            df = pd.read_csv(signals_file)
            if len(df) > 0:
                df['date'] = pd.to_datetime(df['date'])
                if 'time_stop_date' in df.columns:
                    df['time_stop_date'] = pd.to_datetime(df['time_stop_date'], errors='coerce')
                return df
        except Exception as e:
            st.warning(f"Could not load saved signals: {e}")

    return None


def get_saved_signal_for_commodity(commodity):
    """Get saved signal for a specific commodity"""
    signals_df = load_saved_signals()

    if signals_df is not None:
        commodity_signals = signals_df[signals_df['commodity'] == commodity]
        if len(commodity_signals) > 0:
            signal_row = commodity_signals.iloc[-1]  # Get most recent

            return {
                'date': signal_row['date'],
                'signal': signal_row['signal'],
                'confidence': signal_row['confidence'],
                'prediction': signal_row['prediction'],
                'percentile': signal_row['percentile'],
                'current_price': signal_row['current_price'],
                'stop_loss': signal_row['stop_loss'] if signal_row['stop_loss'] != '' else None,
                'profit_target': signal_row['profit_target'] if signal_row['profit_target'] != '' else None,
                'position_size_pct': signal_row['position_size_pct'],
                'atr': signal_row['atr'],
                'time_stop_date': signal_row['time_stop_date'] if pd.notna(signal_row.get('time_stop_date')) else None,
                'is_live': True
            }

    return None


@st.cache_data
def load_validation_results(results_path):
    """Load walk-forward validation results"""
    df = pd.read_csv(results_path)
    return df


@st.cache_data
def load_validation_trades(trades_path):
    """Load walk-forward validation trades"""
    df = pd.read_csv(trades_path)
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date'] = pd.to_datetime(df['exit_date'])
    return df


@st.cache_data
def load_market_data(data_path):
    """Load latest market data"""
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


@st.cache_resource
def load_model(model_dir):
    """Load trained model"""
    try:
        import joblib
        model_path = model_dir / 'model_2024.pkl'
        scaler_path = model_dir / 'scaler_2024.pkl'
        imputer_path = model_dir / 'imputer_2024.pkl'

        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        imputer = joblib.load(imputer_path)

        feature_names = list(imputer.feature_names_in_) if hasattr(imputer, 'feature_names_in_') else None

        return model, imputer, scaler, feature_names
    except Exception as e:
        st.warning(f"Could not load model: {e}")
        return None, None, None, None


def calculate_atr(prices, high=None, low=None, period=20):
    """Calculate Average True Range"""
    if high is not None and low is not None:
        tr1 = high - low
        tr2 = abs(high - prices.shift(1))
        tr3 = abs(low - prices.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    else:
        tr = prices.pct_change().abs().rolling(5).std() * prices

    atr = tr.rolling(period).mean()
    return atr


def generate_live_signal(df, model, imputer, scaler, feature_cols, config):
    """Generate live trading signal from current data"""

    LONG_PERCENTILE = config['parameters']['thresholds']['long_percentile']
    SHORT_PERCENTILE = config['parameters']['thresholds']['short_percentile']
    ROLLING_WINDOW = config['parameters']['thresholds']['rolling_window']
    R_PER_TRADE = config['parameters']['position_sizing']['r_per_trade']
    ATR_MULTIPLIER = config['parameters']['stops']['atr_multiplier']
    ATR_PERIOD = config['parameters']['stops']['atr_period']
    PROFIT_TARGET_R = config['parameters']['profit_targets']['target_r']
    TIME_STOP_DAYS = config['parameters']['stops']['time_stop_days']

    recent_df = df.tail(150).copy()

    features = recent_df[feature_cols].ffill()
    features_imputed = imputer.transform(features)
    features_scaled = scaler.transform(features_imputed)

    predictions = model.predict(features_scaled)
    recent_df['prediction'] = predictions

    recent_df['pred_percentile'] = recent_df['prediction'].rolling(
        ROLLING_WINDOW, min_periods=20
    ).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

    if 'high' in recent_df.columns and 'low' in recent_df.columns:
        recent_df['atr'] = calculate_atr(
            recent_df['close'],
            recent_df['high'],
            recent_df['low'],
            period=ATR_PERIOD
        )
    else:
        recent_df['atr'] = calculate_atr(recent_df['close'], period=ATR_PERIOD)

    today = recent_df[recent_df['pred_percentile'].notna()].iloc[-1]

    signal = None
    position_size = 0
    percentile = today['pred_percentile']

    if percentile >= LONG_PERCENTILE:
        signal = 'LONG'
        position_size = 1.0
    elif percentile <= SHORT_PERCENTILE:
        signal = 'SHORT'
        position_size = 1.0

    if signal:
        current_price = today['close']
        atr = today['atr']
        stop_distance = ATR_MULTIPLIER * atr

        if signal == 'LONG':
            stop_loss = current_price - stop_distance
            profit_target = current_price + (PROFIT_TARGET_R * stop_distance)
        else:
            stop_loss = current_price + stop_distance
            profit_target = current_price - (PROFIT_TARGET_R * stop_distance)

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
            'is_live': True
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
            'is_live': True
        }


def get_most_recent_signal(trades_df):
    """Get the most recent trade as current signal indicator"""

    # Get most recent trade
    recent_trade = trades_df.iloc[-1]

    return {
        'date': recent_trade['exit_date'],
        'signal': recent_trade['direction'],
        'entry_price': recent_trade['entry_price'],
        'exit_price': recent_trade['exit_price'],
        'pnl_r': recent_trade['pnl_r'],
        'exit_reason': recent_trade['exit_reason'],
        'days_held': recent_trade['days_held'],
        'entry_date': recent_trade['entry_date'],
        'is_live': False
    }


def display_terminal_header():
    """Display terminal-style header"""

    st.markdown("""
<div class="terminal-box">
╔═══════════════════════════════╗
║                               ║
║  AG FUTURES SIGNALS           ║
║  HIGH CONVICTION MODELS       ║
║                               ║
║  CORN 🌽  |  SOYBEANS 🫘      ║
║                               ║
╚═══════════════════════════════╝
</div>
    """, unsafe_allow_html=True)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"**SYSTEM TIME:** `{current_time}`")
    st.markdown("**MODEL:** `HIGH_CONVICTION_v2024 | 90th/10th PERCENTILE`")
    st.markdown("**DATA:** `WALK-FORWARD VALIDATION 2014-2025`")
    st.markdown("---")


def display_recent_signal(commodity, signal):
    """Display most recent signal in terminal style"""

    is_live = signal.get('is_live', False)

    if is_live:
        st.markdown(f"### {COMMODITY_CONFIGS[commodity]['emoji']} {COMMODITY_CONFIGS[commodity]['display_name']} - CURRENT SIGNAL 🔴 LIVE")
    else:
        st.markdown(f"### {COMMODITY_CONFIGS[commodity]['emoji']} {COMMODITY_CONFIGS[commodity]['display_name']} - MOST RECENT SIGNAL")

    if is_live:
        # Live signal display
        signal_date = signal['date'].strftime('%Y-%m-%d') if isinstance(signal['date'], pd.Timestamp) else signal['date']
        signal_color = "LONG ↑" if signal['signal'] == 'LONG' else ("SHORT ↓" if signal['signal'] == 'SHORT' else "HOLD")

        if signal['signal'] == 'HOLD':
            box_content = f"""
<div class="terminal-box">
╔══════════════════════════════════╗
║ SIGNAL: HOLD
║ DATE: {signal_date}
║
║ STATUS: NO ACTIVE SIGNAL
║ PRICE: ${signal['current_price']:.2f}
║ PRED: {signal['prediction']:+.2%}
║ PCTL: {signal['percentile']:.1%}
║   (NEED >90% OR <10%)
║
║ [WAITING FOR HIGH CONVICTION]
╚══════════════════════════════════╝
</div>
            """
        else:
            stop_str = f"${signal['stop_loss']:.2f}"
            target_str = f"${signal['profit_target']:.2f}"
            price_str = f"${signal['current_price']:.2f}"
            time_stop_str = str(signal['time_stop_date'])[:10] if signal['time_stop_date'] else 'N/A'

            box_content = f"""
<div class="terminal-box">
╔══════════════════════════════════╗
║ ⚡ SIGNAL: {signal_color}
║ DATE: {signal_date}
║
║ ENTRY: {price_str}
║ STOP: {stop_str}
║ TARGET: {target_str}
║
║ CONFIDENCE: {signal['confidence']:.1%}
║ PERCENTILE: {signal['percentile']:.1%}
║ POSITION: {signal['position_size_pct']:.1f}% equity
║
║ RISK/REWARD: 1:2
║ TIME STOP: {time_stop_str}
║   (10 days)
║
║ [🔴 LIVE SIGNAL]
╚══════════════════════════════════╝
</div>
            """
    else:
        # Historical signal display
        entry_date = signal['entry_date'].strftime('%Y-%m-%d')
        exit_date = signal['date'].strftime('%Y-%m-%d')

        signal_color = "LONG ↑" if signal['signal'] == 'LONG' else "SHORT ↓"
        pnl_display = f"{signal['pnl_r']:+.2f}R"

        entry_px_str = f"${signal['entry_price']:.2f}"
        exit_px_str = f"${signal['exit_price']:.2f}"

        box_content = f"""
<div class="terminal-box">
╔══════════════════════════════════╗
║ LAST TRADE: {signal_color}
║ ENTRY: {entry_date}
║ EXIT: {exit_date}
║
║ ENTRY PX: {entry_px_str}
║ EXIT PX: {exit_px_str}
║ PNL: {pnl_display}
║
║ EXIT RSN: {signal['exit_reason'].upper()}
║ DAYS HELD: {signal['days_held']}
║
║ [HISTORICAL BACKTEST]
╚══════════════════════════════════╝
</div>
        """

    st.markdown(box_content, unsafe_allow_html=True)


def display_ytd_performance(commodity, results_df, trades_df):
    """Display YTD performance metrics"""

    st.markdown(f"### {COMMODITY_CONFIGS[commodity]['emoji']} {COMMODITY_CONFIGS[commodity]['display_name']} - YTD 2024-2025 PERFORMANCE")

    # Get 2024-2025 period
    ytd_results = results_df[results_df['period'] == '2024-2025'].iloc[0]
    ytd_trades = trades_df[trades_df['period'] == '2024-2025'].copy()

    # Calculate metrics
    total_trades = int(ytd_results['total_trades'])
    winning_trades = int(ytd_results['winning_trades'])
    losing_trades = int(ytd_results['losing_trades'])
    win_rate = ytd_results['win_rate']
    total_pnl_r = ytd_results['total_pnl_r']
    sharpe_ratio = ytd_results['sharpe_ratio']
    max_drawdown_r = ytd_results['max_drawdown_r']
    avg_win_r = ytd_results['avg_win_r']
    avg_loss_r = ytd_results['avg_loss_r']

    # Metrics display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("TOTAL PNL", f"{total_pnl_r:.2f}R")
        st.metric("SHARPE", f"{sharpe_ratio:.2f}")

    with col2:
        st.metric("WIN RATE", f"{win_rate:.1%}")
        st.metric("TRADES", f"{total_trades}")

    with col3:
        st.metric("AVG WIN", f"{avg_win_r:.2f}R")
        st.metric("AVG LOSS", f"{avg_loss_r:.2f}R")

    with col4:
        st.metric("MAX DD", f"{max_drawdown_r:.2f}R")
        st.metric("W/L", f"{winning_trades}/{losing_trades}")

    st.markdown("---")


def display_ytd_trades(commodity, trades_df):
    """Display YTD trade history"""

    st.markdown(f"### {COMMODITY_CONFIGS[commodity]['emoji']} {COMMODITY_CONFIGS[commodity]['display_name']} - YTD 2024-2025 TRADE HISTORY")

    ytd_trades = trades_df[trades_df['period'] == '2024-2025'].copy()
    ytd_trades = ytd_trades.sort_values('entry_date', ascending=False)

    # Format for display
    display_trades = ytd_trades[[
        'entry_date', 'exit_date', 'direction',
        'entry_price', 'exit_price', 'pnl_r',
        'exit_reason', 'days_held'
    ]].copy()

    display_trades['entry_date'] = display_trades['entry_date'].dt.strftime('%Y-%m-%d')
    display_trades['exit_date'] = display_trades['exit_date'].dt.strftime('%Y-%m-%d')
    display_trades['entry_price'] = display_trades['entry_price'].apply(lambda x: f"${x:.2f}")
    display_trades['exit_price'] = display_trades['exit_price'].apply(lambda x: f"${x:.2f}")
    display_trades['pnl_r'] = display_trades['pnl_r'].apply(lambda x: f"{x:+.2f}R")

    display_trades.columns = [
        'ENTRY', 'EXIT', 'DIR',
        'ENTRY_PX', 'EXIT_PX', 'PNL',
        'EXIT_RSN', 'DAYS'
    ]

    st.dataframe(
        display_trades,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")


def display_all_periods_summary(commodity, results_df):
    """Display summary of all validation periods"""

    st.markdown(f"### 📊 {COMMODITY_CONFIGS[commodity]['display_name']} - ALL PERIODS WALK-FORWARD VALIDATION")

    # Format for display
    display_results = results_df[[
        'period', 'total_trades', 'win_rate',
        'total_pnl_r', 'sharpe_ratio', 'max_drawdown_r'
    ]].copy()

    display_results['win_rate'] = display_results['win_rate'].apply(lambda x: f"{x:.1%}")
    display_results['total_pnl_r'] = display_results['total_pnl_r'].apply(lambda x: f"{x:+.2f}R")
    display_results['sharpe_ratio'] = display_results['sharpe_ratio'].apply(lambda x: f"{x:.2f}")
    display_results['max_drawdown_r'] = display_results['max_drawdown_r'].apply(lambda x: f"{x:.2f}R")

    display_results.columns = [
        'PERIOD', 'TRADES', 'WIN_RATE',
        'TOTAL_PNL', 'SHARPE', 'MAX_DD'
    ]

    st.dataframe(
        display_results,
        use_container_width=True,
        hide_index=True
    )

    # Summary stats
    st.markdown("#### AGGREGATE STATISTICS")
    col1, col2, col3, col4 = st.columns(4)

    total_pnl_all = results_df['total_pnl_r'].sum()
    avg_win_rate = results_df['win_rate'].mean()
    avg_sharpe = results_df['sharpe_ratio'].mean()
    worst_dd = results_df['max_drawdown_r'].max()

    with col1:
        st.metric("TOTAL PNL (ALL)", f"{total_pnl_all:.2f}R")
    with col2:
        st.metric("AVG WIN RATE", f"{avg_win_rate:.1%}")
    with col3:
        st.metric("AVG SHARPE", f"{avg_sharpe:.2f}")
    with col4:
        st.metric("WORST DD", f"{worst_dd:.2f}R")


def main():
    """Main dashboard application"""

    # Display header
    display_terminal_header()

    # Select commodity
    commodity = st.selectbox(
        "SELECT COMMODITY:",
        options=['corn', 'soybean'],
        format_func=lambda x: f"{COMMODITY_CONFIGS[x]['emoji']} {COMMODITY_CONFIGS[x]['display_name']}"
    )

    config = COMMODITY_CONFIGS[commodity]

    # Check if live data is available
    has_live_data = check_live_data_available(config)

    try:
        # Load validation data (always available)
        with st.spinner(f"LOADING {config['display_name']} DATA..."):
            results_df = load_validation_results(config['validation_results'])
            trades_df = load_validation_trades(config['validation_trades'])

        # Try to load saved signal first (for cloud deployment)
        signal = get_saved_signal_for_commodity(commodity)

        if signal:
            # Saved signal found
            st.success(f"✓ SAVED SIGNAL LOADED | DATE: {signal['date'].strftime('%Y-%m-%d')} | {len(trades_df)} BACKTEST TRADES")
        elif has_live_data:
            # No saved signal, but we have data files - generate live signal
            try:
                with st.spinner("GENERATING LIVE SIGNAL..."):
                    df = load_market_data(config['data_path'])

                    with open(config['config_path'], 'r') as f:
                        model_config = json.load(f)

                    model, imputer, scaler, feature_names = load_model(config['model_dir'])

                    if model is not None and feature_names is not None:
                        signal = generate_live_signal(df, model, imputer, scaler, feature_names, model_config)
                        st.success(f"✓ LIVE DATA LOADED | LATEST: {df['date'].max().strftime('%Y-%m-%d')} | {len(trades_df)} BACKTEST TRADES")
                    else:
                        st.warning("Model files not available - showing historical data only")
                        signal = get_most_recent_signal(trades_df)
            except Exception as e:
                st.warning(f"Could not generate live signal: {e} - showing historical data")
                signal = get_most_recent_signal(trades_df)
        else:
            # No saved signal and no data files - show historical
            signal = get_most_recent_signal(trades_df)
            st.success(f"✓ DATA LOADED | {len(trades_df)} TRADES | PERIODS: 2014-2025")

        st.markdown("---")

        # Display signal (live or historical)
        display_recent_signal(commodity, signal)

        st.markdown("---")

        # Display YTD performance
        display_ytd_performance(commodity, results_df, trades_df)

        # Display YTD trades
        display_ytd_trades(commodity, trades_df)

        # Display all periods summary
        display_all_periods_summary(commodity, results_df)

    except Exception as e:
        st.error(f"❌ ERROR: {str(e)}")
        st.exception(e)

    # Footer
    st.markdown("---")
    st.markdown("""
<div class="terminal-box">
╔═══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  HISTORICAL BACKTEST DATA | NOT FINANCIAL ADVICE                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝
</div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
