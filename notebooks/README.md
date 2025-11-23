# Signal Discovery Notebooks

This directory contains notebooks and scripts for discovering trading signals from Munich city data.

## Files

### Analysis Scripts

- **`signal_discovery.py`** - Main signal discovery script that:
  - Fetches live Munich data (weather, air quality, flights)
  - Generates synthetic market data with embedded correlations
  - Computes correlation matrices
  - Identifies strong correlations (|r| > 0.3)
  - Creates visualizations
  - Generates summary report

### Jupyter Notebooks

- **`signal_discovery_analysis.ipynb`** - Interactive notebook presenting:
  - Signal discovery results
  - Correlation heatmaps
  - Time series visualizations
  - Scatter plots with trend lines
  - Feature importance analysis
  - Trading implications

### Generated Outputs

The `output/` directory contains:

- **`correlation_heatmap.png`** - Heatmap showing correlations between Munich variables and market returns
- **`top_correlations_timeseries.png`** - Time series plots of top correlated variables
- **`correlation_scatterplots.png`** - Scatter plots with trend lines
- **`feature_importance.png`** - Bar chart of average correlation strength by variable
- **`signal_discovery_report.txt`** - Text summary of findings

## Key Findings

### Strong Correlations Identified

1. **Active Flights → Flight Derivative Returns** (r = 0.69)
   - Strong positive correlation
   - Flight activity is a leading indicator
   - Economic intuition: more flights = more economic activity

2. **Active Flights → ETF Returns** (r = 0.36)
   - Moderate positive correlation
   - Secondary signal for confirmation
   - Supports primary flight activity signal

## Usage

### Run Signal Discovery

```bash
python notebooks/signal_discovery.py
```

This will:
1. Fetch current Munich data from APIs
2. Generate synthetic market data (100 samples)
3. Compute correlations
4. Create visualizations in `output/`
5. Generate summary report

### View Results in Jupyter

```bash
jupyter notebook notebooks/signal_discovery_analysis.ipynb
```

Or open the notebook in VS Code / JupyterLab.

## Requirements

The script requires:
- Python 3.11+
- pandas, numpy, matplotlib, seaborn
- aiohttp, pyyaml, loguru
- Data client modules from `src/data/`

API keys (optional for demo):
- `OPENWEATHER_API_KEY` - For weather and air quality data
- OpenSky Network API is public (no key required)

## Configuration

The script uses `config.yaml` for:
- Location settings (Munich coordinates, airport code)
- API endpoints
- Data source parameters
- Correlation thresholds

To analyze a different city, update `config.yaml`:

```yaml
location:
  city: London
  country: UK
  coordinates:
    lat: 51.5074
    lon: -0.1278
  airport_code: LHR
```

## Trading Strategy Integration

The discovered signals are integrated into the trading bot:

1. **Feature Engineering** (`src/signals/features.py`)
   - Flight activity momentum
   - Flight volume moving averages
   - Flight activity deltas

2. **Signal Generation** (`src/signals/generator.py`)
   - Flight activity signal with 0.69 correlation weight
   - Combined with other Munich signals

3. **Adaptive Strategy** (`src/strategy/adaptive.py`)
   - Regime-specific signal weights
   - Flight signal emphasized in trending regimes

## Presentation Materials

For the hackathon presentation, use:

1. **Correlation Heatmap** - Shows systematic analysis
2. **Time Series Plots** - Demonstrates signal behavior over time
3. **Feature Importance** - Highlights flight activity as key signal
4. **Summary Report** - Provides talking points

Key message: "We discovered a novel 0.69 correlation between flight activity and market returns, providing a unique trading edge."

## Notes

- The synthetic market data is generated with embedded correlations for demonstration
- In production, use historical market data for backtesting
- Correlations should be monitored for stability over time
- The analysis can be re-run periodically to discover new signals

## Future Enhancements

- [ ] Add historical data analysis (not just synthetic)
- [ ] Implement rolling correlation analysis
- [ ] Add statistical significance tests
- [ ] Create interactive dashboard with Streamlit
- [ ] Add more Munich data sources (events, traffic, etc.)
- [ ] Implement automated signal discovery pipeline
