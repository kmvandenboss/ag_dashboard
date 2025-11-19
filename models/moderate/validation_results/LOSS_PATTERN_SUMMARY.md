# Loss Pattern Analysis Summary - Moderate V1.0

**Date**: 2025-11-16
**Analysis**: Comprehensive investigation of 232 losing trades (26.8% of all trades)

---

## Executive Summary

Initial analysis revealed a paradox: **losses occurred at lower volatility than winners** (21.9% vs 23.6%). Deeper investigation uncovered that the relationship is **non-linear** - the worst performance occurs in **moderately high volatility** (22.9-27.3%), not low volatility.

---

## Part 1: Basic Loss Characteristics

### Exit Reason Breakdown:
- **55.6% (129 trades)**: Hit stop loss at -1.347R average
- **43.5% (101 trades)**: Hit time stop at -0.400R average
- **0.9% (2 trades)**: Other exits

**Key Insight**: Stop losses are 3.4× more painful than time stops in R terms.

### Temporal Distribution:
- **2020**: 43 losses (18.5% of all losses) - COVID volatility spike
- **Worst month**: 2020-08 with 7 losses averaging -1.495R

### Loss Magnitude:
- **Mean**: -0.926R
- **Median**: -1.035R
- **Worst**: -3.659R
- **Distribution**: 55.6% are "large losses" (≤-1.0R), 44.4% are "small losses" (>-1.0R)

### Direction Balance:
- **Short losses**: 50.9%
- **Long losses**: 49.1%
- **Conclusion**: No directional bias in losses (perfectly balanced)

---

## Part 2: The Volatility Paradox

### Initial Finding:
Losers entered at **LOWER** volatility than winners:
- Losers: 21.88% average entry volatility
- Winners: 23.58% average entry volatility
- Difference: +1.70% (winners entered in higher vol)

This is counterintuitive - we'd expect losses in HIGH volatility.

### Deeper Investigation - Performance by Volatility Quintile:

| Quintile | Vol Range | Trades | Win Rate | Avg R | Status |
|----------|-----------|--------|----------|-------|--------|
| **Q1** (Lowest) | 6.8% - 16.6% | 174 | 66.7% | +0.929R | ⚠️ Below average |
| **Q2** (Low) | 16.7% - 19.9% | 173 | **76.9%** | **+1.250R** | ✅ BEST |
| **Q3** (Mid) | 19.9% - 22.9% | 173 | 73.4% | +1.039R | ✅ Good |
| **Q4** (High) | 22.9% - 27.3% | 173 | 69.4% | +0.787R | ❌ WORST |
| **Q5** (Highest) | 27.3% - 83.4% | 173 | 79.8% | +1.148R | ✅ Very good |

### The U-Shaped Curve:

```
Performance
    ▲
1.30│        Q2 (BEST)
    │         ●
1.20│                        Q5
    │                         ●
1.10│
    │            Q3
1.00│             ●
    │   Q1
0.90│    ●             Q4 (WORST)
    │                   ●
0.80│
    └─────────────────────────────────> Volatility
      Low   Low   Mid   High  Extreme
```

**Interpretation**:
1. **Very low vol (Q1)**: Marginal signals, limited opportunity
2. **Low-moderate vol (Q2)**: Sweet spot - stable trends, reliable signals
3. **Mid vol (Q3)**: Still good performance
4. **Moderately high vol (Q4)**: Choppy, triggers stops, unreliable signals
5. **Extreme vol (Q5)**: Strong directional moves, model captures trends

---

## Part 3: Stop Loss Analysis

### Stop Width Investigation:

| Metric | Winners | Losers | Difference |
|--------|---------|--------|------------|
| Entry volatility | 23.58% | 21.88% | +1.70% |
| Entry ATR | $5.507 | $4.866 | +$0.642 |
| Stop width (% of price) | 4.12% | 3.89% | +0.23% |
| Entry price level | $451.13 | $428.01 | +$23.13 |

**Stop Loss Trades** (129 trades):
- Entry volatility: 21.21% (low end)
- Stop width: 3.82%
- Average loss: **-1.347R**

**Time Stop Losses** (101 trades):
- Entry volatility: 22.84% (higher)
- Stop width: 4.01%
- Average loss: **-0.400R**

**Insight**: Stop loss trades entered at LOWER volatility and resulted in much larger losses. This suggests:
- In low volatility, subtle patterns may be less reliable
- Positions have less "room to breathe" in tight ranges
- Small adverse moves quickly trigger stops

---

## Part 4: Volatility Regime Transitions

### Expanding vs Contracting Volatility:

| Regime at Entry | Winners | Losers |
|-----------------|---------|--------|
| Expanding volatility | 373 (58.8%) | 123 (53.0%) |
| Contracting volatility | 261 (41.2%) | 109 (47.0%) |

**Finding**: Losers are **more likely during contracting volatility** regimes.
- Winners: 58.8% entered during expanding vol
- Losers: Only 53.0% entered during expanding vol
- **Conclusion**: Model struggles when volatility is decreasing (shifting market dynamics)

---

## Part 5: Actionable Recommendations

### ❌ Do NOT Implement:
1. **Minimum volatility filter** - Would filter Q1/Q2, but Q2 is our BEST quintile!
2. **Avoid low volatility** - The problem is Q4 (moderately high vol), not low vol

### ✅ Consider Testing:

#### Recommendation #1: Avoid the "Dead Zone" (Q4 volatility range)
- **Problem**: Q4 (22.9-27.3% vol) has worst performance (+0.787R, 69.4% win rate)
- **Solution**: Skip or reduce position size when 20-day volatility is 23-27%
- **Expected impact**: Filter 173 trades (20%), remove ~53 losses
- **Risk**: Also filters ~120 winners, but they're below-average winners
- **Test this as**: Moderate v1.6

#### Recommendation #2: Dynamic stop multiplier based on volatility
- **Problem**: Fixed 3.5× ATR gives inconsistent risk across regimes
- **Solution**:
  - Low vol (Q1-Q2): Use 4.0× ATR (wider in % terms)
  - Mid vol (Q3): Use 3.5× ATR (current)
  - High vol (Q4-Q5): Use 3.0× ATR (tighter in % terms)
- **Expected impact**: More consistent stop width across conditions
- **Risk**: May increase whipsaws in Q5 (extreme vol)

#### Recommendation #3: Position sizing by volatility quintile
- **Problem**: All quintiles traded equally, but performance varies 37% (Q2 vs Q4)
- **Solution**:
  - Q2 (best): 1.0× base position
  - Q1, Q3, Q5: 0.75× base position
  - Q4 (worst): 0.5× base position or skip
- **Expected impact**: Concentrate capital in favorable conditions
- **Risk**: Reduces diversification

#### Recommendation #4: Filter contracting volatility regimes
- **Problem**: 47% of losers entered during contracting vol (vs 41% of winners)
- **Solution**: Skip trades when current volatility < 10-day average volatility
- **Expected impact**: Filters regime transitions when model may struggle
- **Risk**: May miss early trend entries
- **Test this as**: Moderate v1.7

---

## Part 6: Most Promising Next Steps

### Priority 1: Test Q4 Volatility Filter (Moderate v1.6)
Skip or reduce exposure when 20-day volatility is 23-27%.

**Hypothesis**: The "moderately high volatility" zone is choppy and unreliable. Avoiding it could improve:
- Win rate (filter worst quintile)
- Average R (remove low-quality trades)
- Sharpe ratio (smoother equity curve)

**Expected metrics**:
- Trades: ~690 (down from 866, -20%)
- Win rate: ~74% (up from 71.6%)
- Avg R: Improved (removing worst performers)

### Priority 2: Test Contracting Volatility Filter (Moderate v1.7)
Skip trades when volatility is decreasing vs recent average.

**Hypothesis**: Model struggles during regime transitions. Filtering these could:
- Reduce losses in shifting conditions
- Improve win rate
- Sacrifice some trade frequency for quality

**Expected metrics**:
- Trades: ~650 (down from 866, -25%)
- Win rate: ~73%+ (filter 47% of losers vs 41% of winners)
- Sharpe: Improved stability

---

## Conclusion

The "low volatility paradox" is actually a **moderately high volatility problem**:

1. ✅ **Low-moderate vol (Q2)**: Best performance zone
2. ❌ **Moderately high vol (Q4)**: Worst performance zone
3. ✅ **Extreme vol (Q5)**: Good performance (strong trends)

**Root causes of losses**:
- Stop losses hit harder in lower volatility (-1.347R) than time stops (-0.400R)
- Model struggles in contracting volatility regimes
- Q4 volatility range (22.9-27.3%) is a "dead zone" with choppy, unreliable signals

**Most actionable insight**: Avoid the Q4 "dead zone" and/or contracting volatility regimes.

---

## Files Generated

1. `loss_analysis_detailed.csv` - All 232 losing trades with full details
2. `volatility_regime_analysis.csv` - All 866 trades enriched with market conditions
3. `performance_by_volatility_quintile.csv` - Quintile breakdown
4. `volatility_recommendations.csv` - Actionable recommendations

**Next session**: Test Moderate v1.6 with Q4 volatility filter or v1.7 with contracting volatility filter.
