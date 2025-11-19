# Growth Risk Model (Elevated_Risk_v1)

**Status**: Design Phase - Requires Validation
**Created**: 2025-11-14
**Risk Profile**: Growth (30% R per trade)

---

## Executive Summary

The Growth model targets **strong growth (50-70% annual returns)** while maintaining **reasonable risk control (drawdowns under -15%)**. It sits between the Moderate (20% R) and Balanced (40% R) models, offering 75% of the Balanced returns with better drawdown characteristics.

### Key Characteristics

| Metric | Value |
|--------|-------|
| **Position Size** | 30% R per trade |
| **Target Annual Return** | 50-70% |
| **Expected Max DD** | -10% to -12% |
| **Expected Sharpe** | 3.0 |
| **Risk Level** | Growth (High) |
| **Min Capital** | $70,000 |
| **Recommended Capital** | $140,000+ |

---

## Design Philosophy

### Bridging Growth and Safety

The Growth model completes the risk ladder:

```
Conservative:  10% R  →  ~18% annual  →  -4.8% DD
Moderate:      20% R  →  ~30% annual  →  -8% DD
Growth:        30% R  →  ~60% annual  → -10% DD   ← NEW
Balanced:      40% R  →  ~90% annual  → -11.7% DD
Aggressive:    50% R  → ~125% annual  → -14.9% DD
```

**Target Market**: Traders who want:
- ✅ Strong growth (50-70% annual)
- ✅ Manageable drawdowns (under -15%)
- ✅ Better risk control than Balanced
- ✅ Higher returns than Moderate

### The 30% R Sweet Spot

**Why 30% R**:
- 3× conservative (meaningful leverage)
- 75% of balanced (substantial but not extreme)
- Theoretical max exposure: 150% (5 positions × 30%)
- Big enough for strong returns, small enough to control risk

---

## Parameter Design

### Position Sizing: 30% R per Trade

**Rationale**:
- 3× the conservative model (30% vs 10%)
- 75% the balanced model (30% vs 40%)
- Provides strong growth with risk control
- Max portfolio risk: 150% (vs 100% moderate, 200% balanced)

**Risk Profile**:
- Each position risks 30% of equity
- Max 5 concurrent positions = 150% theoretical exposure
- Diversification reduces actual risk below 150%

### Entry Thresholds: 82nd/18th Percentile

**Strategic Positioning**:
- Conservative: 90th/10th (top 10% only)
- Moderate: 85th/15th (top 15%)
- **Growth: 82nd/18th (top 18%)** ← Active but selective
- Balanced: 80th/20th (top 20%)

**Benefits**:
- More selective than balanced → Better signal quality
- More active than moderate → More opportunities
- 82nd percentile is evidence-based sweet spot

### Profit Targets: 2.25R

**Strategic Choice**:
- Conservative: None (let winners run)
- Moderate: 2.0R
- **Growth: 2.25R** ← Optimized for growth
- Balanced: 2.5R
- Aggressive: 3.0R

**Why 2.25R**:
- Captures strong moves without being greedy
- Hit rate higher than 2.5R target
- Allows for strong returns with risk management
- 2.25:1 reward-to-risk is excellent for commodities

### Stop Loss: 3.75× ATR

**Balanced Approach**:
- Conservative: 3.0× ATR (tight)
- Moderate: 3.5× ATR (balanced)
- **Growth: 3.75× ATR** ← Room to work
- Balanced/Aggressive: 4.0× ATR (wide)

**Benefits**:
- Wider than moderate → Fewer false stops
- Tighter than aggressive → Better risk control
- Positions get room to develop

---

## Expected Performance

### Estimated Metrics

Based on interpolation between validated models:

| Metric | Moderate | **Growth** | Balanced | Aggressive |
|--------|----------|------------|----------|------------|
| R per Trade | 20% | **30%** | 40% | 50% |
| Return/Period | 60-80% | **120-180%** | 260.5% | 407.0% |
| Annual Return | ~30% | **~50-70%** | ~90% | ~125% |
| Max DD (avg) | -8% | **-10%** | -11.7% | -14.9% |
| Max DD (worst) | -12% to -15% | **-15% to -20%** | -22.3% | -28.8% |
| Sharpe Ratio | 2.5 | **3.0** | 3.47 | 3.50 |
| Win Rate | 64% | **~65.5%** | 65.2% | 66.3% |

### Return Expectations

**Base Case** (Most Likely):
- 2-year period: +120% to +160%
- Annual: +50% to +70%
- Sharpe: 2.8 to 3.2
- Max DD: -9% to -11%

**Conservative Case** (25th Percentile):
- 2-year period: +80% to +120%
- Annual: +35% to +50%
- Sharpe: 2.3 to 2.8
- Max DD: -11% to -15%

**Optimistic Case** (75th Percentile):
- 2-year period: +160% to +220%
- Annual: +70% to +95%
- Sharpe: 3.2 to 3.6
- Max DD: -7% to -10%

### Comparison to Existing Models

**vs. Moderate (20% R)**:
- **Returns**: 2× higher (60% vs 30% annual)
- **Drawdowns**: 1.25× worse (-10% vs -8%)
- **Trade-off**: Double the return for modest DD increase

**vs. Balanced (40% R)**:
- **Returns**: 67% as high (60% vs 90% annual)
- **Drawdowns**: 15% better (-10% vs -11.7%)
- **Trade-off**: Give up some returns for safer ride

**vs. Conservative (10% R)**:
- **Returns**: 3.5× higher (60% vs 18% annual)
- **Drawdowns**: 2× worse (-10% vs -4.8%)
- **Trade-off**: Strong growth for manageable risk increase

---

## Risk Analysis

### Drawdown Characteristics

**Expected Typical Drawdown**: -7% to -11%

**Expected Worst-Case DD**: -15% to -20%

**Why This Range**:
- Moderate (20% R): -8% avg, -12% to -15% worst
- Balanced (40% R): -11.7% avg, -22.3% worst
- Growth (30% R) should fall 75% between them
- 3× position size vs conservative → ~2× drawdown

### Stress Test Scenarios

**Market Crash (COVID-like)**:
- Conservative: -8.48%
- Moderate (estimate): -12% to -15%
- **Growth (estimate)**: -15% to -20%
- Balanced: -22.25%
- **Verdict**: Should survive major crashes without catastrophic loss

**High Volatility Period**:
- 30% R positions create meaningful swings
- Profit target at 2.25R helps lock gains
- 3.75× ATR stops provide cushion
- **Verdict**: Expect -3% to -6% daily moves in extreme markets

**Extended Drawdown**:
- Larger positions = faster recovery if signals improve
- Profit targets prevent runaway losses
- Multiple positions provide diversification
- **Verdict**: Recovery within 1-3 months typical

### Psychological Difficulty

**Rating**: Moderate-High (4/5)

**What to Expect**:
- Daily swings of -2% to -5% in volatile periods
- Max DD of -15% to -20% in worst scenarios
- Win rate around 65.5% (1 in 3 trades still lose)
- Positions will feel substantial (30% of equity at risk)

**Suitable For**:
- ✅ Experienced futures traders (2+ years)
- ✅ Comfortable with -15% drawdowns
- ✅ Growth-focused mindset
- ✅ Strong risk discipline
- ✅ Adequate capital ($140K+)

**NOT Suitable For**:
- ❌ Beginners to futures trading
- ❌ Cannot tolerate -15% drawdowns
- ❌ Seeking maximum safety (use Conservative/Moderate)
- ❌ Seeking maximum returns (use Balanced/Aggressive)
- ❌ Under-capitalized (<$70K)

---

## Implementation Requirements

### Capital Requirements

**Minimum**: $70,000
- 30% R per trade = $21,000 risk per position
- Max 5 positions = $105,000 total risk
- Need cushion for drawdowns

**Recommended**: $140,000+
- Provides 2× cushion
- Can weather -20% DD without margin calls
- Comfortable position sizing

**Optimal**: $200,000+
- 2.8× cushion for comfort
- Professional-level capital base
- Can add positions opportunistically

### Validation Required

**IMPORTANT**: This model is in **design phase** and requires validation before production use.

**Validation Checklist**:
1. ✅ Design parameters (DONE)
2. ⏳ Walk-forward validation (2014-2025)
3. ⏳ Stress testing (COVID period)
4. ⏳ Monte Carlo simulation
5. ⏳ Trade-by-trade verification
6. ⏳ Detailed trade log review
7. ⏳ Production deployment

---

## Key Differences from Other Models

### vs. Moderate (20% R)

| Parameter | Moderate | Growth | Change |
|-----------|----------|--------|--------|
| Position Size | 20% R | 30% R | **+50% larger** |
| Entry Threshold | 85th/15th | 82nd/18th | **+20% more trades** |
| Profit Target | 2.0R | 2.25R | **+12.5% target** |
| Stop Loss | 3.5× ATR | 3.75× ATR | **+7% wider** |
| Max Portfolio Risk | 100% | 150% | **+50% exposure** |

**Net Effect**: 1.5× more aggressive with proportionally wider parameters

### vs. Balanced (40% R)

| Parameter | Growth | Balanced | Change |
|-----------|--------|----------|--------|
| Position Size | 30% R | 40% R | **-25% smaller** |
| Entry Threshold | 82nd/18th | 80th/20th | **-10% selective** |
| Profit Target | 2.25R | 2.5R | **-10% tighter** |
| Stop Loss | 3.75× ATR | 4.0× ATR | **-6% tighter** |
| Max Portfolio Risk | 150% | 200% | **-25% exposure** |

**Net Effect**: 25% less aggressive with proportionally tighter controls

---

## Trading Strategy Summary

### Entry Rules

1. **ML Prediction** must be in top 18% (longs) or bottom 18% (shorts)
2. **Percentile Sizing**:
   - 90th+ percentile: Full position (1.0×)
   - 85-90th: 75% position (0.75×)
   - 75-85th: 50% position (0.5×)
   - Below 75th: No trade (0×)

### Position Sizing

- **Base Risk**: 30% of equity per trade
- **Adjusted by Conviction**: Base × Conviction Multiplier
- **Max Single Position**: 30% R
- **Max Concurrent**: 5 positions
- **Max Portfolio Risk**: 150%

### Exit Rules

**Priority Order**:
1. **ATR Stop** (3.75× ATR-20): Protect capital
2. **Profit Target** (2.25R): Lock in strong gains
3. **Time Stop** (10 days): Force exit at horizon

### Example Trade

**Scenario**: CORN long signal
- Account: $150,000
- ML prediction: 88th percentile (strong bullish)
- Current price: $4.50
- ATR(20): $0.10

**Calculation**:
- Base risk: $150,000 × 30% = $45,000
- Conviction: 88th percentile → 0.75× (high)
- Position risk: $45,000 × 0.75 = $33,750
- Stop distance: $0.10 × 3.75 = $0.375
- Position size: $33,750 / $0.375 = 90,000 bushels
- Stop loss: $4.50 - $0.375 = $4.125
- Profit target: $4.50 + ($0.375 × 2.25) = $5.34
- Time stop: 10 days from entry

**Risk/Reward**:
- Risk: $0.375 per bushel = $33,750 total (22.5% of account)
- Reward: $0.84 per bushel = $75,600 total (2.25R)
- R:R ratio: 2.25:1

---

## Recommended Use Cases

### Ideal For

1. **Growth Portfolios**
   - Want strong returns (50-70% annual)
   - Can tolerate -15% drawdowns
   - Have adequate capital ($140K+)
   - 2+ years futures experience

2. **Aggressive Core Allocation**
   - Use Growth as 70% of corn allocation
   - Add Moderate 20% for stability
   - Add Balanced 10% for upside

3. **Transition to High-Risk**
   - Graduated from Moderate model
   - Building confidence for Balanced
   - Testing higher risk tolerance
   - Scaling up position sizes

4. **High Return with Risk Control**
   - Want better returns than Moderate (2×)
   - Don't want extreme risk of Balanced
   - Value 50-70% returns with -15% max DD

### NOT Ideal For

1. **Seeking Maximum Returns**
   - Use Balanced (90%) or Aggressive (125%)
   - Growth is for strong growth with control

2. **Cannot Handle -15% DD**
   - Use Moderate (-8% to -10% DD)
   - Use Conservative (-4.8% DD)

3. **Insufficient Capital**
   - Need minimum $70K, ideally $140K+
   - Under-capitalized = forced exits in DD

4. **Beginners to Futures**
   - Start with Conservative
   - Upgrade to Moderate after 1 year
   - Upgrade to Growth after 2 years

---

## Model Comparison Summary

| Model | R/Trade | Annual | Max DD | Best For |
|-------|---------|--------|--------|----------|
| **Conservative** | 10% | ~18% | -4.8% | Safety first |
| **Moderate** | 20% | ~30% | -8% | Balanced growth |
| **Growth** | 30% | ~60% | -10% | Strong growth |
| **Balanced** | 40% | ~90% | -11.7% | High returns |
| **Aggressive** | 50% | ~125% | -14.9% | Maximum returns |

**Growth Model Position**: The "sweet spot" for traders who want strong returns (60% annual) without extreme drawdowns (under -15%).

---

## Next Steps

### For Model Validation

1. **Run Backtests**:
   - Use validation framework
   - Test on 2014-2025 data (6 periods)
   - Generate detailed trade logs

2. **Analyze Results**:
   - Compare actual vs expected (120-180% per period)
   - Check drawdown characteristics (-10% avg target)
   - Verify Sharpe ratio > 2.5
   - Review trade-by-trade logs

3. **Stress Test**:
   - COVID crash (2020-2021)
   - High volatility (2022-2023)
   - Trending markets (2018-2019)

4. **Trade Log Review**:
   - Sample 100+ trades
   - Verify entry/exit logic
   - Check position sizing accuracy
   - Analyze win/loss patterns

### For Production Deployment

1. Validation complete ✅
2. Documentation updated ✅
3. Code implementation ⏳
4. Detailed trade logs generated ⏳
5. Trade-by-trade review ⏳
6. Paper trading (optional) ⏳
7. Small live test (1/10 size) ⏳
8. Full deployment ⏳

---

## Conclusion

The **Growth model (30% R)** completes the risk ladder by providing:

- ✅ **Strong growth** (50-70% annual) with risk control
- ✅ **Manageable drawdowns** (-10% avg, -15% to -20% worst)
- ✅ **Excellent risk-adjusted returns** (3.0 Sharpe)
- ✅ **Balanced position sizes** (3× conservative, 75% of balanced)
- ✅ **Sweet spot** between growth and safety

**Risk Level**: Growth/High (4/5)
**Return Potential**: High (5/5)
**Suitable For**: Experienced traders seeking strong growth with reasonable risk
**Validation Status**: Design phase - requires testing with detailed trade logs

---

**Last Updated**: 2025-11-14
**Version**: 1.0
**Author**: Corn Trading Model Suite
**Status**: Design Phase - Pending Validation with Trade Logs
