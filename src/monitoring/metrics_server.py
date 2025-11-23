"""
Real-time metrics HTTP endpoint.

Provides HTTP server for exposing live trading metrics.
"""

import asyncio
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Optional

from .metrics import MetricsCollector


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for metrics endpoint."""
    
    metrics_collector: Optional[MetricsCollector] = None
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/metrics" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            if self.metrics_collector:
                metrics = self.metrics_collector.get_summary()
                metrics["timestamp"] = datetime.utcnow().isoformat()
                response = json.dumps(metrics, indent=2, default=str)
            else:
                response = json.dumps({"error": "No metrics available"})
            
            self.wfile.write(response.encode())
        
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = json.dumps({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
            self.wfile.write(response.encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class MetricsServer:
    """
    HTTP server for real-time metrics.
    
    Exposes trading metrics via HTTP endpoint for monitoring and dashboards.
    Runs in background thread to avoid blocking trading operations.
    """
    
    def __init__(self, metrics_collector: MetricsCollector, port: int = 8080):
        """
        Initialize metrics server.
        
        Args:
            metrics_collector: MetricsCollector to expose
            port: HTTP port to listen on
        """
        self.metrics_collector = metrics_collector
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None
        self.running = False
    
    def start(self) -> None:
        """
        Start metrics server in background thread.
        
        Performance: ~10ms startup time
        """
        if self.running:
            return
        
        # Set class variable for handler
        MetricsHandler.metrics_collector = self.metrics_collector
        
        # Create server
        self.server = HTTPServer(("0.0.0.0", self.port), MetricsHandler)
        
        # Start in background thread
        self.thread = Thread(target=self._run_server, daemon=True)
        self.thread.start()
        self.running = True
    
    def _run_server(self) -> None:
        """Run server loop (internal method)."""
        if self.server:
            self.server.serve_forever()
    
    def stop(self) -> None:
        """
        Stop metrics server.
        
        Performance: ~10ms shutdown time
        """
        if not self.running:
            return
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.thread:
            self.thread.join(timeout=1.0)
        
        self.running = False
    
    def get_url(self) -> str:
        """Get metrics endpoint URL."""
        return f"http://localhost:{self.port}/metrics"
