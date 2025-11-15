"""
Simple HTTP Health Check Endpoint for NATS Services
Minimal implementation for ECS Fargate health checks
"""

import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    
    nats_client = None
    is_healthy = True
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            # Check if service is healthy
            healthy = self.__class__.is_healthy
            
            # Check NATS connection if available
            if self.__class__.nats_client:
                try:
                    nc = getattr(self.__class__.nats_client, 'nc', None)
                    if nc:
                        healthy = healthy and nc.is_connected
                except:
                    healthy = False
            
            if healthy:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'OK\n')
            else:
                self.send_response(503)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Service Unavailable\n')
        else:
            # 404 for other paths
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress access logs."""
        pass


def start_health_check_server(port: int = 8080, nats_client = None):
    """
    Start health check HTTP server in background thread.
    
    Args:
        port: Port to listen on (default 8080)
        nats_client: Optional NATS client to monitor
    
    Returns:
        HTTPServer instance
    """
    # Set class variables for handler
    HealthCheckHandler.nats_client = nats_client
    HealthCheckHandler.is_healthy = True
    
    # Create server
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    
    # Start in background thread
    def serve():
        logger.info(f"Health check server listening on port {port}")
        server.serve_forever()
    
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    
    logger.info(f"Health check endpoint started: http://0.0.0.0:{port}/health")
    return server


def stop_health_check_server(server):
    """Stop the health check server."""
    if server:
        server.shutdown()
        logger.info("Health check server stopped")

