"""
Report generation for trading sessions.

Creates summary reports and visualizations of trading performance.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .metrics import MetricsCollector


class ReportGenerator:
    """
    Generates session summary reports.
    
    Creates human-readable and machine-readable reports of trading performance,
    including statistics, regime breakdowns, and trade history.
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for report output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_session_summary(
        self,
        metrics: MetricsCollector,
        session_start: datetime,
        session_end: datetime,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive session summary.
        
        Args:
            metrics: MetricsCollector with session data
            session_start: Session start time
            session_end: Session end time
            additional_info: Additional context to include
        
        Returns:
            Dictionary with complete session summary
        
        Performance: ~5ms
        """
        summary = metrics.get_summary()
        
        # Add session metadata
        duration = (session_end - session_start).total_seconds()
        summary["session"] = {
            "start_time": session_start.isoformat(),
            "end_time": session_end.isoformat(),
            "duration_seconds": duration,
            "duration_hours": duration / 3600
        }
        
        # Add additional info
        if additional_info:
            summary["additional_info"] = additional_info
        
        # Calculate derived metrics
        if summary["trade_count"] > 0:
            summary["avg_pnl_per_trade"] = summary["total_pnl"] / summary["trade_count"]
            summary["trades_per_hour"] = summary["trade_count"] / max(duration / 3600, 0.01)
        else:
            summary["avg_pnl_per_trade"] = 0.0
            summary["trades_per_hour"] = 0.0
        
        return summary
    
    def save_summary_json(
        self,
        summary: Dict,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save summary as JSON file.
        
        Args:
            summary: Summary dictionary
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to saved file
        
        Performance: ~10ms
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"session_summary_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return output_path
    
    def save_summary_text(
        self,
        summary: Dict,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save summary as human-readable text file.
        
        Args:
            summary: Summary dictionary
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to saved file
        
        Performance: ~10ms
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"session_summary_{timestamp}.txt"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("TRADING SESSION SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            # Session info
            if "session" in summary:
                f.write("Session Information:\n")
                f.write(f"  Start: {summary['session']['start_time']}\n")
                f.write(f"  End: {summary['session']['end_time']}\n")
                f.write(f"  Duration: {summary['session']['duration_hours']:.2f} hours\n\n")
            
            # Performance metrics
            f.write("Performance Metrics:\n")
            f.write(f"  Total PnL: ${summary['total_pnl']:.2f}\n")
            f.write(f"  Sharpe Ratio: {summary['sharpe_ratio']:.3f}\n")
            f.write(f"  Max Drawdown: {summary['max_drawdown']*100:.2f}%\n")
            f.write(f"  Current Drawdown: {summary['current_drawdown']*100:.2f}%\n")
            f.write(f"  Win Rate: {summary['win_rate']*100:.2f}%\n\n")
            
            # Trade statistics
            f.write("Trade Statistics:\n")
            f.write(f"  Total Trades: {summary['trade_count']}\n")
            f.write(f"  Winning Trades: {summary['winning_trades']}\n")
            f.write(f"  Losing Trades: {summary['losing_trades']}\n")
            if summary['trade_count'] > 0:
                f.write(f"  Avg PnL per Trade: ${summary.get('avg_pnl_per_trade', 0):.2f}\n")
                f.write(f"  Trades per Hour: {summary.get('trades_per_hour', 0):.2f}\n")
            f.write("\n")
            
            # Regime performance
            if "regime_performance" in summary and summary["regime_performance"]:
                f.write("Performance by Regime:\n")
                for regime, stats in summary["regime_performance"].items():
                    f.write(f"  {regime}:\n")
                    f.write(f"    Total PnL: ${stats['total_pnl']:.2f}\n")
                    f.write(f"    Trades: {stats['trade_count']}\n")
                    f.write(f"    Avg PnL: ${stats['avg_pnl_per_trade']:.2f}\n")
                f.write("\n")
            
            # Recent performance
            if "recent_sharpe" in summary:
                f.write("Recent Performance:\n")
                f.write(f"  Recent Sharpe (last 20 trades): {summary['recent_sharpe']:.3f}\n\n")
            
            f.write("=" * 80 + "\n")
        
        return output_path
    
    def generate_and_save_report(
        self,
        metrics: MetricsCollector,
        session_start: datetime,
        session_end: datetime,
        additional_info: Optional[Dict] = None
    ) -> tuple[Path, Path]:
        """
        Generate and save both JSON and text reports.
        
        Args:
            metrics: MetricsCollector with session data
            session_start: Session start time
            session_end: Session end time
            additional_info: Additional context to include
        
        Returns:
            Tuple of (json_path, text_path)
        
        Performance: ~20ms
        """
        summary = self.generate_session_summary(
            metrics, session_start, session_end, additional_info
        )
        
        json_path = self.save_summary_json(summary)
        text_path = self.save_summary_text(summary)
        
        return json_path, text_path
