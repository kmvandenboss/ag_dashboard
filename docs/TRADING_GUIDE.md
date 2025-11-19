# Trading Signals Guide

Complete guide to using AG Futures Production signals for trading corn and soybean futures.

## Signal Format

Daily signals are generated in this format:

```
================================================================================
🌽 CORN FUTURES - DAILY SIGNAL
================================================================================
Date: 2025-11-18
Model: Moderate (20% R)

📊 Signal: LONG
   Confidence: 72.0% (Percentile: 85.3%)

📈 Entry:
   Price: $4.50
   Position Size: 20.0% of equity

🎯 Risk Management:
   Stop Loss: $4.15 (7.8% below entry)
   Profit Target: $5.20 (15.6% above entry)
   Risk/Reward: 1:2.0
   Time Stop: 2025-11-28 (10 days)

📊 Technical:
   Predicted Return: +2.3% (10-day)
   ATR (20-day): $0.10

================================================================================
⚠️  This is a signal, not financial advice. Trade at your own risk.
================================================================================
```

---

## Signal Types

### LONG (Buy)

**When**: Model prediction in top 20% (or top 10% for high conviction)

**Action**: Enter long position (buy futures)

**Interpretation**:
- Model expects corn/soybean prices to rise over next 10 days
- Strong bullish setup based on fundamentals, sentiment, weather, and technicals

**Example Triggers**:
- Poor crop conditions (< 50% good/excellent)
- Tight WASDE stocks-to-use ratio (< 12%)
- Extreme put/call ratio (fear > 80th percentile)
- Strong technical momentum

### SHORT (Sell)

**When**: Model prediction in bottom 20% (or bottom 10% for high conviction)

**Action**: Enter short position (sell futures)

**Interpretation**:
- Model expects prices to fall over next 10 days
- Bearish setup

**Example Triggers**:
- Excellent crop conditions (> 70% good/excellent)
- Abundant WASDE stocks (stocks-to-use > 18%)
- Extreme call buying (greed < 20th percentile)
- Weak technical momentum

### HOLD (No Trade)

**When**: Model prediction between 20th and 80th percentile

**Action**: No position / flat

**Interpretation**:
- No strong directional edge
- Wait for clearer signal
- Preserve capital

---

## Position Sizing

### Fixed-R Method (Recommended)

**R** = Risk per trade as % of account equity

**Models**:
- **Moderate**: 20% R per trade
- **Growth**: 30% R per trade
- **High Conviction**: Variable (10-30% R based on confidence)
- **Conservative v2.0**: 10-15% R per trade

### Calculation Example

**Scenario**:
- Account: $100,000
- Model: Moderate (20% R)
- Signal: LONG corn @ $4.50
- ATR: $0.10
- Stop: 3.5× ATR = $0.35

**Position Size**:
```
Risk per trade = $100,000 × 20% = $20,000
Stop distance = $0.35 per bushel
Contracts = $20,000 / ($0.35 × 5,000 bushels)
          = $20,000 / $1,750
          = 11.4 contracts → 11 contracts

Actual risk = 11 × $1,750 = $19,250 (19.25% R) ✓
```

**Note**: 1 corn contract = 5,000 bushels

### Conviction-Based Sizing

High conviction models adjust position size by confidence:

| Percentile | Conviction | Position Size |
|------------|------------|---------------|
| **> 95th** | Extreme | 100% (1.0× base R) |
| **90-95th** | Very High | 75% (0.75× base R) |
| **85-90th** | High | 50% (0.5× base R) |
| **< 85th** | None | 0% (no trade) |

**Example**:
- Base R = 20%
- Percentile = 92nd
- Adjusted R = 20% × 0.75 = 15%

---

## Risk Management

### Stop Loss (3.5× ATR)

**Purpose**: Protect capital, exit losing trades

**Calculation**:
```
ATR = Average True Range (20-day)
Stop Distance = 3.5 × ATR

LONG: Stop = Entry - (3.5 × ATR)
SHORT: Stop = Entry + (3.5 × ATR)
```

**Why 3.5× ATR**:
- Wider than 2-3× ATR: Fewer false stops
- Tighter than 5× ATR: Better risk control
- Allows for normal volatility

**Execution**: Use stop-loss orders, not mental stops

### Profit Target (2.0R)

**Purpose**: Lock in winners, take profits systematically

**Calculation**:
```
Target Distance = 2.0 × Stop Distance

LONG: Target = Entry + (2.0 × Stop Distance)
SHORT: Target = Entry - (2.0 × Stop Distance)
```

**Example**:
- Entry: $4.50
- Stop: $4.15 (distance = $0.35)
- Target: $4.50 + (2.0 × $0.35) = $5.20

**Why 2.0R**:
- Achievable in 10 days
- Good risk/reward ratio
- Higher than 1.5R, lower than 3.0R (sweet spot)

**Note**: High conviction models may not use profit targets (let winners run).

### Time Stop (10 Days)

**Purpose**: Force exits on stale positions

**Rule**: Close position after 10 days regardless of profit/loss

**Rationale**:
- Model predicts 10-day returns
- Holding longer = outside model scope
- Prevent capital from being tied up

### Exit Priority

When multiple exit signals trigger:

1. **Stop Loss** (highest priority - protect capital)
2. **Profit Target** (lock in wins)
3. **Time Stop** (force exit at horizon)

---

## Trade Execution

### Daily Routine

**1. Morning (Before Market)**
- Review overnight news (USDA reports, weather, geopolitics)
- Check for major crop/weather events

**2. After Market Close (4-5 PM ET)**
```bash
# Update data
python scripts/update_all.py

# Generate signals
python scripts/generate_signals.py
```

**3. Review Signal**
- Check signal type (LONG/SHORT/HOLD)
- Verify confidence level
- Calculate position size
- Set stop loss and profit target

**4. Place Orders (Next Morning)**
- Use limit orders near yesterday's close
- Set protective stops immediately
- Set profit target orders

**5. Monitor Position**
- Check stops daily
- Adjust for new signals (if signal changes)
- Exit at 10 days if still open

### Order Types

**Entry**:
- **Limit Order**: Set at yesterday's close ± $0.05
- **Market Order**: If urgent (use sparingly)

**Stop Loss**:
- **Stop-Loss Order**: Guaranteed exit (may slip in fast markets)

**Profit Target**:
- **Limit Order**: Take profit at target price

**Time Stop**:
- **Market Order**: Exit on day 10

---

## Signal Interpretation

### High Confidence Signals (> 80th Percentile)

**Characteristics**:
- Multiple factors aligned (fundamentals + sentiment + technicals)
- Model very confident in direction

**Action**:
- Enter full position size
- Set stops and targets
- Hold conviction

**Example**:
```
Percentile: 92nd
Confidence: 92%
→ Very strong LONG signal
→ Position: 100% of base R
```

### Medium Confidence (70-80th Percentile)

**Characteristics**:
- Some factors aligned, not all
- Model moderately confident

**Action**:
- Enter reduced position (50-75% of base R)
- Tighter stops
- Be ready to exit quickly

### Low Confidence (< 70th Percentile)

**Characteristics**:
- Marginal signal
- Mixed factors

**Action**:
- Consider skipping trade
- Or very small position (25% of base R)
- Extra vigilant on risk management

---

## Multi-Model Approach

### Using Multiple Models

**Benefits**:
- Diversified strategies
- Smoother equity curve
- Confirmation signals

**Example Portfolio**:
```
Corn Allocation: $100,000
├─ Moderate: $60,000 (60%, core position)
├─ Conservative: $20,000 (20%, stability)
└─ High Conviction: $20,000 (20%, upside)
```

### Signal Aggregation

**When models agree**:
- **All LONG**: High confidence, enter full size
- **All SHORT**: High confidence, enter full size

**When models disagree**:
- **Mixed signals**: Reduce size or wait
- **Example**: Moderate says LONG, Growth says HOLD → Enter 50% size

**When models neutral**:
- **All HOLD**: Stay flat, preserve capital

---

## Real-World Examples

### Example 1: Strong LONG Signal

**Setup**:
- Date: July 15, 2024
- Crop conditions plummet to 48% good/excellent (poor crop)
- WASDE stocks-to-use at 10.5% (very tight)
- Put/call ratio at 85th percentile (fear)
- Model percentile: 94th

**Signal**:
```
LONG Corn @ $5.20
Stop: $4.85 (3.5× ATR = $0.35)
Target: $5.90 (2.0R)
Position: 20% R = 12 contracts
```

**Outcome** (Hypothetical):
- Price rallies to $5.95 in 8 days
- Exit at profit target $5.90
- Gain: $0.70 × 5,000 × 12 = $42,000
- Return: +42% on risk (2.1R)

### Example 2: Whipsaw Loss

**Setup**:
- Date: March 10, 2024
- Model percentile: 82nd (borderline)
- Mixed fundamentals

**Signal**:
```
LONG Corn @ $4.30
Stop: $4.00 (3.5× ATR = $0.30)
Target: $4.90
Position: 20% R = 13 contracts
```

**Outcome**:
- Price drops to $4.00 next day, stop hit
- Loss: $0.30 × 5,000 × 13 = $19,500
- Return: -19.5% on account (1.0R loss)

**Lesson**: Accept losses, part of system

### Example 3: Time Stop Exit

**Setup**:
- Signal: LONG @ $4.50
- Stop: $4.15
- Target: $5.20

**Outcome**:
- Day 1-10: Price bounces between $4.40-$4.60
- Day 10: Price at $4.55, time stop triggered
- Exit @ $4.55
- Gain: $0.05 × 5,000 × 11 = $2,750
- Return: +2.75% (0.14R)

**Lesson**: Small win, capital freed for better signals

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Ignoring Stop Losses

**Problem**: "I'll wait for it to come back"

**Result**: Small loss becomes catastrophic

**Solution**: Always use stop-loss orders

### ❌ Mistake 2: Over-Sizing Positions

**Problem**: Risk 50% on one trade (way above 20% R)

**Result**: Single loss wipes out account

**Solution**: Stick to model position sizes

### ❌ Mistake 3: Trading Every Signal

**Problem**: Trade even 60th percentile signals

**Result**: Low-quality trades, reduced win rate

**Solution**: Only trade strong signals (> 75th percentile)

### ❌ Mistake 4: Moving Stops

**Problem**: Move stop further away when losing

**Result**: Larger losses

**Solution**: Set stop at entry, never move it further away

### ❌ Mistake 5: Taking Profits Too Early

**Problem**: Exit at $4.70 when target is $5.20

**Result**: Miss big winners

**Solution**: Let targets be hit, trust the system

---

## Performance Expectations

### Realistic Outcomes

**Win Rate**: 60-75% (meaning 25-40% of trades will lose)

**Average Win**: +1.5R to +2.5R

**Average Loss**: -0.8R to -1.0R (some stops slipped)

**Sharpe Ratio**: 0.45 to 5.80 (depends on model)

**Max Drawdown**: -12% to -20% (depending on model)

**Annual Return**: 20% to 60% (depending on model and risk)

### Drawdown Psychology

**Expect**:
- 3-5 consecutive losses occasionally
- -10% to -15% drawdowns annually
- Winning months followed by flat/losing months

**How to Handle**:
- Reduce size during drawdowns (risk 15% vs 20%)
- Don't abandon system after 3 losses
- Review signals, not psychology
- Take breaks if stressed

---

## Advanced Techniques

### Scaling In

**Method**: Enter partial position, add on confirmation

**Example**:
- Signal: LONG @ $4.50 (82nd percentile)
- Enter 50% size: 6 contracts
- If price confirms (up $0.10), add 50%: 6 more contracts

**Benefit**: Reduce risk on borderline signals

### Scaling Out

**Method**: Exit position in stages

**Example**:
- Position: 12 contracts
- Exit 50% at 1.5R profit
- Exit remaining 50% at 2.5R profit

**Benefit**: Lock partial profits, ride winners

### Filtering Signals

**Method**: Only trade signals that align with macro trends

**Example**:
- WASDE shows declining stocks → Only take LONG signals
- Excellent crop conditions → Only take SHORT signals

**Benefit**: Higher win rate, fewer whipsaws

---

## Signal Logging

All signals are logged to `signals/signal_history.csv`:

```csv
date,signal,confidence,prediction,percentile,current_price,stop_loss,profit_target,position_size_pct,atr,time_stop_date
2025-11-18,LONG,0.72,0.023,0.853,4.50,4.15,5.20,20.0,0.10,2025-11-28
```

**Use this to**:
- Track performance
- Calculate win rate
- Analyze what works
- Refine strategy

---

## Summary Checklist

**Before Every Trade**:
- [ ] Data updated (`python scripts/update_all.py`)
- [ ] Signal generated (`python scripts/generate_signals.py`)
- [ ] Position size calculated (R × contracts)
- [ ] Stop loss calculated (3.5× ATR)
- [ ] Profit target calculated (2.0R)
- [ ] Orders placed (entry, stop, target)

**During Trade**:
- [ ] Monitor stop daily
- [ ] Check for signal changes
- [ ] Track days in position
- [ ] Log trade in journal

**After Trade**:
- [ ] Record outcome in spreadsheet
- [ ] Calculate actual R (profit/loss vs risk)
- [ ] Review what worked/didn't
- [ ] Update performance metrics

---

## Disclaimer

**Trading futures involves substantial risk of loss.** Past performance does not guarantee future results. These signals are for educational purposes only, not financial advice. Only trade with capital you can afford to lose. Consult a licensed financial advisor before trading.

---

**Next Steps**:
1. Start with paper trading (simulate trades)
2. Use small position sizes initially (10% R vs 20% R)
3. Build confidence over 20-30 trades
4. Scale up gradually as you gain experience

For model details, see [MODELS.md](MODELS.md).
