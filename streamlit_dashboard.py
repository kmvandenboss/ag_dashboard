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

    /* Terminal box style */
    .terminal-box {
        background-color: #0a0a0a;
        border: 2px solid #00ff00;
        padding: 20px;
        font-family: 'Courier New', monospace;
        color: #00ff00;
        white-space: pre;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Base directory
BASE_DIR = Path(__file__).parent

# Commodity configurations
COMMODITY_CONFIGS = {
    'corn': {
        'validation_results': BASE_DIR / 'models' / 'corn_high_conviction' / 'validation_results' / 'walk_forward_6period_results.csv',
        'validation_trades': BASE_DIR / 'models' / 'corn_high_conviction' / 'validation_results' / 'walk_forward_6period_trades.csv',
        'display_name': 'CORN',
        'emoji': '🌽'
    },
    'soybean': {
        'validation_results': BASE_DIR / 'models' / 'soy_high_conviction' / 'validation_results' / 'walk_forward_6period_results.csv',
        'validation_trades': BASE_DIR / 'models' / 'soy_high_conviction' / 'validation_results' / 'walk_forward_6period_trades.csv',
        'display_name': 'SOYBEANS',
        'emoji': '🫘'
    }
}


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
        'entry_date': recent_trade['entry_date']
    }


def display_terminal_header():
    """Display terminal-style header"""

    st.markdown("""
<div class="terminal-box">
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                       AG FUTURES SIGNALS DASHBOARD                            ║
║                          HIGH CONVICTION MODELS                               ║
║                                                                               ║
║                    CORN 🌽  |  SOYBEANS 🫘                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
</div>
    """, unsafe_allow_html=True)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f"**SYSTEM TIME:** `{current_time}`")
    st.markdown("**MODEL:** `HIGH_CONVICTION_v2024 | 90th/10th PERCENTILE`")
    st.markdown("**DATA:** `WALK-FORWARD VALIDATION 2014-2025`")
    st.markdown("---")


def display_recent_signal(commodity, signal):
    """Display most recent signal in terminal style"""

    st.markdown(f"### {COMMODITY_CONFIGS[commodity]['emoji']} {COMMODITY_CONFIGS[commodity]['display_name']} - MOST RECENT SIGNAL")

    entry_date = signal['entry_date'].strftime('%Y-%m-%d')
    exit_date = signal['date'].strftime('%Y-%m-%d')

    signal_color = "LONG ↑" if signal['signal'] == 'LONG' else "SHORT ↓"
    pnl_display = f"{signal['pnl_r']:+.2f}R"

    # Format prices with proper spacing
    entry_px_str = f"${signal['entry_price']:.2f}"
    exit_px_str = f"${signal['exit_price']:.2f}"

    box_content = f"""
<div class="terminal-box">
┌─────────────────────────────────────────────────────────────────┐
│ LAST TRADE: {signal_color:<50} │
│ ENTRY:      {entry_date:<50} │
│ EXIT:       {exit_date:<50} │
│                                                                 │
│ ENTRY PX:   {entry_px_str:<50} │
│ EXIT PX:    {exit_px_str:<50} │
│ PNL:        {pnl_display:<50} │
│                                                                 │
│ EXIT RSN:   {signal['exit_reason'].upper():<50} │
│ DAYS HELD:  {signal['days_held']:<50} │
│                                                                 │
│ [HISTORICAL BACKTEST DATA - NOT LIVE TRADING]                   │
└─────────────────────────────────────────────────────────────────┘
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

    try:
        # Load data
        with st.spinner(f"LOADING {config['display_name']} DATA..."):
            results_df = load_validation_results(config['validation_results'])
            trades_df = load_validation_trades(config['validation_trades'])

        st.success(f"✓ DATA LOADED | {len(trades_df)} TRADES | PERIODS: 2014-2025")

        st.markdown("---")

        # Display most recent signal
        recent_signal = get_most_recent_signal(trades_df)
        display_recent_signal(commodity, recent_signal)

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
