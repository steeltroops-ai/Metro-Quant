"""
Visualization module for trading bot presentation.

Generates charts for signal discovery, performance analysis, and regime adaptation.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path

from loguru import logger


class ChartGenerator:
    """
    Generates presentation-quality charts for trading bot analysis.
    
    Creates visualizations for:
    - Signal discovery correlation heatmaps
    - PnL curves with regime breakdowns
    - Regime transition timelines
    - Consistency metrics dashboards
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize chart generator.
        
        Args:
            output_dir: Directory to save generated charts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style for presentation-quality charts
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 11
        
        logger.info(f"ChartGenerator initialized, output_dir={output_dir}")
    
    def generate_correlation_heatmap(
        self,
        features: pd.DataFrame,
        market_returns: pd.Series,
        title: str = "Signal Discovery: Feature-Return Correlations",
        filename: str = "correlation_heatmap.png"
    ) -> str:
        """
        Generate correlation heatmap between features and market returns.
        
        Args:
            features: DataFrame with engineered features
            market_returns: Series of market returns
            title: Chart title
            filename: Output filename
            
        Returns:
            Path to saved chart
            
        Performance: ~100ms
        """
        # Combine features with returns
        data = features.copy()
        data['market_returns'] = market_returns
        
        # Calculate correlation matrix
        corr_matrix = data.corr()
        
        # Extract correlations with market returns
        feature_corrs = corr_matrix['market_returns'].drop('market_returns')
        
        # Sort by absolute correlation
        feature_corrs_sorted = feature_corrs.abs().sort_values(ascending=False)
        top_features = feature_corrs_sorted.head(15).index
        
        # Create heatmap for top features
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Get correlation values for top features
        corr_values = feature_corrs[top_features].values.reshape(-1, 1)
        
        # Create heatmap
        sns.heatmap(
            corr_values,
            annot=True,
            fmt='.3f',
            cmap='RdYlGn',
            center=0,
            vmin=-1,
            vmax=1,
            yticklabels=top_features,
            xticklabels=['Market Returns'],
            cbar_kws={'label': 'Correlation'},
            ax=ax
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel('Features', fontsize=12)
        
        plt.tight_layout()
        
        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Correlation heatmap saved to {output_path}")
        return str(output_path)
    
    def generate_pnl_curve(
        self,
        timestamps: List[datetime],
        pnl_values: List[float],
        regime_labels: Optional[List[str]] = None,
        title: str = "Performance: PnL Over Time",
        filename: str = "pnl_curve.png"
    ) -> str:
        """
        Generate PnL curve with optional regime breakdown.
        
        Args:
            timestamps: List of trade timestamps
            pnl_values: Cumulative PnL at each timestamp
            regime_labels: Optional regime classification at each point
            title: Chart title
            filename: Output filename
            
        Returns:
            Path to saved chart
            
        Performance: ~150ms
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Convert to arrays
        times = pd.to_datetime(timestamps)
        pnl = np.array(pnl_values)
        
        # Plot main PnL curve
        ax.plot(times, pnl, linewidth=2, label='Cumulative PnL', color='#2E86AB')
        
        # Add regime coloring if provided
        if regime_labels:
            regime_colors = {
                'trending': '#A23B72',
                'mean-reverting': '#F18F01',
                'high-volatility': '#C73E1D',
                'low-volatility': '#6A994E',
                'uncertain': '#CCCCCC'
            }
            
            # Color background by regime
            current_regime = regime_labels[0] if regime_labels else None
            regime_start = 0
            
            for i in range(1, len(regime_labels)):
                if regime_labels[i] != current_regime or i == len(regime_labels) - 1:
                    # Regime changed or end of data
                    regime_end = i
                    color = regime_colors.get(current_regime, '#CCCCCC')
                    ax.axvspan(
                        times[regime_start],
                        times[regime_end],
                        alpha=0.2,
                        color=color,
                        label=f'{current_regime}' if current_regime not in ax.get_legend_handles_labels()[1] else ""
                    )
                    current_regime = regime_labels[i]
                    regime_start = i
        
        # Add zero line
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        # Formatting
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Cumulative PnL ($)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"PnL curve saved to {output_path}")
        return str(output_path)
    
    def generate_regime_timeline(
        self,
        timestamps: List[datetime],
        regimes: List[str],
        strategy_params: List[Dict],
        title: str = "Adaptive Strategy: Regime Transitions",
        filename: str = "regime_timeline.png"
    ) -> str:
        """
        Generate timeline showing regime transitions and strategy adjustments.
        
        Args:
            timestamps: List of regime detection timestamps
            regimes: List of regime classifications
            strategy_params: List of strategy parameters at each point
            title: Chart title
            filename: Output filename
            
        Returns:
            Path to saved chart
            
        Performance: ~200ms
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        # Convert to datetime
        times = pd.to_datetime(timestamps)
        
        # Map regimes to numeric values for plotting
        regime_map = {
            'trending': 4,
            'mean-reverting': 3,
            'high-volatility': 2,
            'low-volatility': 1,
            'uncertain': 0
        }
        regime_values = [regime_map.get(r, 0) for r in regimes]
        
        # Plot 1: Regime timeline
        regime_colors = {
            'trending': '#A23B72',
            'mean-reverting': '#F18F01',
            'high-volatility': '#C73E1D',
            'low-volatility': '#6A994E',
            'uncertain': '#CCCCCC'
        }
        
        for i in range(len(times) - 1):
            color = regime_colors.get(regimes[i], '#CCCCCC')
            ax1.plot(
                [times[i], times[i+1]],
                [regime_values[i], regime_values[i]],
                linewidth=4,
                color=color,
                solid_capstyle='butt'
            )
        
        # Add regime labels
        ax1.set_yticks(list(regime_map.values()))
        ax1.set_yticklabels(list(regime_map.keys()))
        ax1.set_ylabel('Market Regime', fontsize=12)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Plot 2: Strategy parameter adjustments
        # Extract a key parameter (e.g., position size multiplier)
        if strategy_params and len(strategy_params) > 0:
            # Try to extract position_multiplier or similar
            param_values = []
            for params in strategy_params:
                if isinstance(params, dict):
                    param_values.append(params.get('position_multiplier', 1.0))
                else:
                    param_values.append(1.0)
            
            ax2.plot(times, param_values, linewidth=2, marker='o', markersize=4, color='#2E86AB')
            ax2.fill_between(times, param_values, alpha=0.3, color='#2E86AB')
            ax2.set_ylabel('Position Size Multiplier', fontsize=12)
            ax2.set_xlabel('Time', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=1.0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Baseline')
            ax2.legend(loc='best')
        
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Regime timeline saved to {output_path}")
        return str(output_path)
    
    def generate_consistency_dashboard(
        self,
        metrics: Dict[str, float],
        regime_performance: Dict[str, Dict[str, float]],
        title: str = "Consistency Metrics Dashboard",
        filename: str = "consistency_dashboard.png"
    ) -> str:
        """
        Generate dashboard highlighting consistency metrics.
        
        Args:
            metrics: Dictionary of overall performance metrics
            regime_performance: Performance breakdown by regime
            title: Chart title
            filename: Output filename
            
        Returns:
            Path to saved chart
            
        Performance: ~250ms
        """
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main metrics (top row, spanning 2 columns)
        ax_main = fig.add_subplot(gs[0, :2])
        ax_main.axis('off')
        
        # Display key metrics prominently
        main_metrics_text = f"""
        CONSISTENCY METRICS (Primary Focus)
        
        Sharpe Ratio: {metrics.get('sharpe_ratio', 0.0):.3f}
        Max Drawdown: {metrics.get('max_drawdown', 0.0)*100:.2f}%
        Win Rate: {metrics.get('win_rate', 0.0)*100:.1f}%
        
        PERFORMANCE METRICS (Secondary)
        
        Total PnL: ${metrics.get('total_pnl', 0.0):.2f}
        Total Trades: {metrics.get('trade_count', 0)}
        """
        
        ax_main.text(
            0.1, 0.5, main_metrics_text,
            fontsize=14,
            verticalalignment='center',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3)
        )
        
        # Sharpe ratio gauge (top right)
        ax_sharpe = fig.add_subplot(gs[0, 2])
        self._plot_gauge(
            ax_sharpe,
            metrics.get('sharpe_ratio', 0.0),
            'Sharpe Ratio',
            vmin=-2,
            vmax=3,
            target=1.5
        )
        
        # Drawdown gauge (middle left)
        ax_dd = fig.add_subplot(gs[1, 0])
        self._plot_gauge(
            ax_dd,
            metrics.get('max_drawdown', 0.0) * 100,
            'Max Drawdown (%)',
            vmin=0,
            vmax=30,
            target=20,
            reverse=True
        )
        
        # Win rate gauge (middle center)
        ax_wr = fig.add_subplot(gs[1, 1])
        self._plot_gauge(
            ax_wr,
            metrics.get('win_rate', 0.0) * 100,
            'Win Rate (%)',
            vmin=0,
            vmax=100,
            target=55
        )
        
        # Recent Sharpe (middle right)
        ax_recent = fig.add_subplot(gs[1, 2])
        self._plot_gauge(
            ax_recent,
            metrics.get('recent_sharpe', 0.0),
            'Recent Sharpe (20 trades)',
            vmin=-2,
            vmax=3,
            target=1.5
        )
        
        # Regime performance breakdown (bottom row)
        ax_regime = fig.add_subplot(gs[2, :])
        
        if regime_performance:
            regimes = list(regime_performance.keys())
            pnls = [regime_performance[r].get('total_pnl', 0.0) for r in regimes]
            trade_counts = [regime_performance[r].get('trade_count', 0) for r in regimes]
            
            x = np.arange(len(regimes))
            width = 0.35
            
            ax_regime.bar(x - width/2, pnls, width, label='Total PnL', color='#2E86AB')
            ax_regime_twin = ax_regime.twinx()
            ax_regime_twin.bar(x + width/2, trade_counts, width, label='Trade Count', color='#F18F01', alpha=0.7)
            
            ax_regime.set_xlabel('Market Regime', fontsize=12)
            ax_regime.set_ylabel('Total PnL ($)', fontsize=12, color='#2E86AB')
            ax_regime_twin.set_ylabel('Trade Count', fontsize=12, color='#F18F01')
            ax_regime.set_title('Performance by Market Regime', fontsize=12, fontweight='bold')
            ax_regime.set_xticks(x)
            ax_regime.set_xticklabels(regimes, rotation=45, ha='right')
            ax_regime.grid(True, alpha=0.3, axis='y')
            ax_regime.legend(loc='upper left')
            ax_regime_twin.legend(loc='upper right')
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Consistency dashboard saved to {output_path}")
        return str(output_path)
    
    def _plot_gauge(
        self,
        ax,
        value: float,
        label: str,
        vmin: float,
        vmax: float,
        target: float,
        reverse: bool = False
    ):
        """
        Plot a gauge chart for a single metric.
        
        Args:
            ax: Matplotlib axis
            value: Current value
            label: Metric label
            vmin: Minimum value
            vmax: Maximum value
            target: Target value
            reverse: If True, lower is better
        """
        # Normalize value to [0, 1]
        norm_value = (value - vmin) / (vmax - vmin)
        norm_value = np.clip(norm_value, 0, 1)
        
        # Determine color based on performance
        if reverse:
            # Lower is better (e.g., drawdown)
            if value <= target:
                color = '#6A994E'  # Green
            elif value <= target * 1.2:
                color = '#F18F01'  # Orange
            else:
                color = '#C73E1D'  # Red
        else:
            # Higher is better (e.g., Sharpe, win rate)
            if value >= target:
                color = '#6A994E'  # Green
            elif value >= target * 0.8:
                color = '#F18F01'  # Orange
            else:
                color = '#C73E1D'  # Red
        
        # Create gauge
        ax.barh(0, norm_value, height=0.3, color=color, alpha=0.7)
        ax.barh(0, 1, height=0.3, color='lightgray', alpha=0.3)
        
        # Add target line
        norm_target = (target - vmin) / (vmax - vmin)
        ax.axvline(x=norm_target, color='black', linestyle='--', linewidth=2, label=f'Target: {target}')
        
        # Add value text
        ax.text(0.5, 0, f'{value:.2f}', ha='center', va='center', fontsize=14, fontweight='bold')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)
        ax.set_title(label, fontsize=11, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
    
    def generate_architecture_diagram(
        self,
        filename: str = "architecture_diagram.png"
    ) -> str:
        """
        Generate system architecture diagram.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved diagram
            
        Performance: ~300ms
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.axis('off')
        
        # Define layers and components
        layers = [
            {
                'name': 'External Data Sources',
                'components': ['Weather API', 'Air Quality API', 'Flight Data', 'Exchange API'],
                'color': '#E8F4F8'
            },
            {
                'name': 'Data Ingestion Layer',
                'components': ['API Clients', 'Data Validators', 'Cache Manager'],
                'color': '#B8E6F0'
            },
            {
                'name': 'Signal Processing Layer',
                'components': ['Feature Engineer', 'Signal Generator', 'Signal Combiner'],
                'color': '#88D8E8'
            },
            {
                'name': 'Strategy Layer',
                'components': ['Regime Detector', 'Adaptive Strategy', 'Position Sizer'],
                'color': '#58CAE0'
            },
            {
                'name': 'Risk Management Layer',
                'components': ['Position Limiter', 'Drawdown Monitor', 'Safe Mode Controller'],
                'color': '#F18F01'
            },
            {
                'name': 'Execution Layer',
                'components': ['Order Manager', 'Position Tracker', 'Exchange Client'],
                'color': '#A23B72'
            },
            {
                'name': 'Monitoring & Logging',
                'components': ['Logger', 'Metrics Collector', 'Report Generator'],
                'color': '#6A994E'
            }
        ]
        
        # Draw layers
        y_start = 0.95
        layer_height = 0.12
        layer_spacing = 0.01
        
        for i, layer in enumerate(layers):
            y = y_start - i * (layer_height + layer_spacing)
            
            # Draw layer box
            rect = plt.Rectangle(
                (0.05, y - layer_height),
                0.9,
                layer_height,
                facecolor=layer['color'],
                edgecolor='black',
                linewidth=2
            )
            ax.add_patch(rect)
            
            # Add layer name
            ax.text(
                0.5, y - layer_height/2,
                layer['name'],
                ha='center', va='center',
                fontsize=12, fontweight='bold'
            )
            
            # Add components
            comp_text = ' | '.join(layer['components'])
            ax.text(
                0.5, y - layer_height + 0.02,
                comp_text,
                ha='center', va='bottom',
                fontsize=9,
                style='italic'
            )
            
            # Draw arrow to next layer
            if i < len(layers) - 1:
                ax.arrow(
                    0.5, y - layer_height - 0.005,
                    0, -layer_spacing + 0.01,
                    head_width=0.03,
                    head_length=0.005,
                    fc='black',
                    ec='black'
                )
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title('Trading Bot Architecture', fontsize=16, fontweight='bold', pad=20)
        
        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Architecture diagram saved to {output_path}")
        return str(output_path)
