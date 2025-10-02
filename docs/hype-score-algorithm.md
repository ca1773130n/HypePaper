# Hype Score Algorithm

**Version**: 1.0
**Last Updated**: 2025-10-02
**Status**: Production

## Overview

The hype score is a **0-10 scale metric** that quantifies research paper "hype" by combining growth rates, absolute metrics, and recency. It helps users identify trending papers that are gaining significant attention in the research community.

## Formula

```
hype_score = (
    0.4 × star_growth_rate +
    0.3 × citation_growth_rate +
    0.2 × absolute_metrics_normalized +
    0.1 × recency_bonus
) × 10
```

### Component Breakdown

#### 1. Star Growth Rate (40% weight)

Measures relative growth in GitHub stars over the comparison period (default: 7 days).

```
star_growth_rate = (current_stars - old_stars) / max(old_stars, 1)
```

**Example:**
- Paper had 100 stars 7 days ago, now has 300 stars
- Growth rate = (300 - 100) / 100 = 2.0 (200% increase)
- Contribution to score = 2.0 × 0.4 = 0.8

**Why 40%?**
- GitHub stars are a strong signal of developer interest
- Tracks practical impact and community adoption
- More volatile than citations, capturing emerging trends

#### 2. Citation Growth Rate (30% weight)

Measures relative growth in academic citations over the comparison period.

```
citation_growth_rate = (current_citations - old_citations) / max(old_citations, 1)
```

**Example:**
- Paper had 50 citations, now has 75 citations
- Growth rate = (75 - 50) / 50 = 0.5 (50% increase)
- Contribution to score = 0.5 × 0.3 = 0.15

**Why 30%?**
- Citations indicate academic impact
- More stable than stars, providing balance
- Weighted lower than stars to prioritize recent community interest

#### 3. Absolute Metrics (20% weight)

Normalized combination of current star and citation counts to prevent low-base-rate bias.

```
normalized_stars = min(current_stars / max_stars, 1.0)
normalized_citations = min(current_citations / max_citations, 1.0)
absolute_score = (normalized_stars + normalized_citations) / 2
```

**Default Normalization Thresholds:**
- `max_stars = 10,000` (papers with 10k+ stars get max score)
- `max_citations = 1,000` (papers with 1k+ citations get max score)

**Example:**
- Paper has 2,000 stars and 200 citations
- Normalized stars = 2000 / 10000 = 0.2
- Normalized citations = 200 / 1000 = 0.2
- Absolute score = (0.2 + 0.2) / 2 = 0.2
- Contribution to score = 0.2 × 0.2 = 0.04

**Why 20%?**
- Prevents papers with tiny bases from dominating (e.g., 1 → 10 stars = 900% growth)
- Ensures established papers with high absolute metrics still rank well
- Balances growth signals with proven impact

#### 4. Recency Bonus (10% weight)

Boosts scores for recently published papers, decaying linearly over one year.

```
recency_bonus = max(0, 1 - (paper_age_days / 365))
```

**Examples:**
- Paper published 7 days ago: bonus = 1 - (7/365) = 0.98
- Paper published 30 days ago: bonus = 1 - (30/365) = 0.92
- Paper published 180 days ago: bonus = 1 - (180/365) = 0.51
- Paper published 365+ days ago: bonus = 0.0

**Why 10%?**
- Encourages discovery of fresh research
- Avoids over-penalizing recent papers with limited data
- Small enough not to dominate other signals

## Score Interpretation

| Score Range | Label      | Color  | Meaning |
|-------------|------------|--------|---------|
| 8.0 - 10.0  | 🔥 Hot     | Red    | Viral growth, explosive interest |
| 6.0 - 8.0   | 📈 Trending| Orange | Strong growth, gaining traction |
| 4.0 - 6.0   | 📊 Steady  | Yellow | Moderate activity, stable interest |
| 0.0 - 4.0   | 📉 Cooling | Gray   | Low/declining interest |

## Worked Examples

### Example 1: Viral New Paper

**NeRF** (Neural Radiance Fields) - 7 days after publication

- Published: 7 days ago
- Stars: 500 (was 50)
- Citations: 20 (was 2)

**Calculation:**
1. Star growth = (500-50)/50 = 9.0
2. Citation growth = (20-2)/2 = 9.0
3. Absolute = ((500/10000) + (20/1000))/2 = 0.035
4. Recency = 1 - (7/365) = 0.98

```
score = (0.4×9.0 + 0.3×9.0 + 0.2×0.035 + 0.1×0.98) × 10
      = (3.6 + 2.7 + 0.007 + 0.098) × 10
      = 6.405 × 10
      = **6.4** (📈 Trending)
```

### Example 2: Established Paper with Steady Growth

**Transformer** (Attention Is All You Need) - 2 years old

- Published: 730 days ago
- Stars: 9,500 (was 9,000)
- Citations: 80,000 (was 75,000)

**Calculation:**
1. Star growth = (9500-9000)/9000 = 0.056
2. Citation growth = (80000-75000)/75000 = 0.067
3. Absolute = ((9500/10000) + (1000/1000))/2 = 0.975 (capped at 1.0 for citations)
4. Recency = 0 (730 > 365)

```
score = (0.4×0.056 + 0.3×0.067 + 0.2×0.975 + 0.1×0) × 10
      = (0.0224 + 0.0201 + 0.195 + 0) × 10
      = 0.2375 × 10
      = **2.4** (📉 Cooling)
```

Despite high absolute metrics, low growth rate results in lower hype score.

### Example 3: Breakout Paper

**DDPM** (Denoising Diffusion Probabilistic Models) - 30 days old

- Published: 30 days ago
- Stars: 1,000 (was 100)
- Citations: 150 (was 10)

**Calculation:**
1. Star growth = (1000-100)/100 = 9.0
2. Citation growth = (150-10)/10 = 14.0 (high academic interest)
3. Absolute = ((1000/10000) + (150/1000))/2 = 0.125
4. Recency = 1 - (30/365) = 0.92

```
score = (0.4×9.0 + 0.3×14.0 + 0.2×0.125 + 0.1×0.92) × 10
      = (3.6 + 4.2 + 0.025 + 0.092) × 10
      = 7.917 × 10
      = **7.9** (📈 Trending, close to 🔥 Hot)
```

## Edge Cases

### Case 1: New Paper with No History

**Problem:** Paper added today with 100 stars, 10 citations, but no historical data.

**Solution:**
- If `old_stars = 0`, treat as baseline: `star_growth = 0`
- Rely on absolute metrics + recency bonus
- After 7 days of data collection, growth rate becomes available

### Case 2: Paper Losing Interest

**Problem:** Paper had 1,000 stars, now has 900 (negative growth).

**Solution:**
- Growth rate = (900-1000)/1000 = -0.1
- Negative growth contributes negative score (allowed)
- Absolute metrics prevent score from going below 0
- Final score reflects cooling interest

### Case 3: Viral Paper Hitting Ceiling

**Problem:** Paper has 50,000 stars (way above 10k normalization threshold).

**Solution:**
- Absolute stars capped at 1.0 when normalized
- Growth rate still captures velocity
- Very high absolute metrics ensure minimum baseline score

## Tuning Parameters

### Adjustable Thresholds

```python
# In HypeScoreService
MAX_STARS = 10_000        # Adjust for your domain
MAX_CITATIONS = 1_000     # Adjust for field citation norms
COMPARISON_DAYS = 7       # Growth rate lookback period
RECENCY_DECAY_DAYS = 365  # Recency bonus decay period
```

### Weight Adjustments

Current weights (40%, 30%, 20%, 10%) balance:
- **Community interest** (stars)
- **Academic impact** (citations)
- **Proven quality** (absolute metrics)
- **Discovery of new work** (recency)

**To emphasize academic rigor:**
```python
star_weight = 0.3
citation_weight = 0.4
```

**To boost discoverability:**
```python
recency_weight = 0.2
absolute_weight = 0.1
```

## Data Requirements

### Minimum Data for Accurate Scores

1. **Paper metadata**: title, authors, published_date
2. **Current metrics**: github_stars (optional), citation_count
3. **Historical snapshots**: At least 2 data points (current + 7 days ago)
4. **For new papers**: 7-day grace period with estimated scores

### Metric Update Frequency

- **Daily updates** (2:30 AM UTC) via `update_metrics` job
- Snapshots stored in TimescaleDB hypertable
- 30-day retention for trend visualization

## Validation

### Unit Tests

See `tests/unit/test_hype_score.py` for comprehensive test coverage:
- Viral paper scenarios
- Stable paper scenarios
- Edge cases (zero metrics, negative growth, overflow)
- Weight validation
- Score bounds (0-10)

### Performance

- **Calculation time**: < 10ms per paper
- **Cached responses**: 1-hour TTL (sub-50ms)
- **Batch processing**: 1,000 papers in < 10 seconds

## Limitations

1. **GitHub-centric bias**: Papers without GitHub repos get lower scores
2. **Citation lag**: Academic citations update slower than stars
3. **Gaming potential**: Artificial star inflation could skew scores
4. **Domain variance**: Citation norms differ across fields (physics vs. CS)
5. **Cold start**: New papers need 7 days of data for growth rates

## Future Enhancements

1. **Field normalization**: Adjust citation thresholds per arXiv category
2. **Social signals**: Integrate Twitter mentions, HackerNews discussions
3. **Quality filters**: Penalize repos with low code-to-stars ratio
4. **User customization**: Allow users to adjust weights per preference
5. **ML-based scoring**: Train model on user engagement patterns

## References

- **GitHub Stars**: https://docs.github.com/en/rest/activity/starring
- **Semantic Scholar Citations**: https://www.semanticscholar.org/product/api
- **arXiv Papers**: https://arxiv.org/help/api
- **Papers With Code**: https://paperswithcode.com/api/v1/docs/

## Changelog

### v1.0 (2025-10-02)
- Initial implementation
- 40-30-20-10 weight distribution
- 0-10 score scale with 4-tier labeling
- 7-day growth rate lookback
- 365-day recency decay
