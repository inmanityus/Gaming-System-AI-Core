"""
Health Check HTTP Endpoint for NATS Services
Provides simple HTTP health check that ECS can use
"""

import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HealthCheckServer:
    """Simple HTTP server for health checks."""
    
    def __init__(self, port: int = 8080, nats_client = None):
        """
        Initialize health check server.
        
        Args:
            port: Port to listen on (default 8080)
            nats_client: Optional NATS client to verify connection
        """
        self.port = port
        self.nats_client = nats_client
        self.server = None
        self.is_healthy = True
    
    async def handle_request(self, reader, writer):
        """Handle incoming health check requests."""
        try:
            # Read request
            request = await reader.read(1024)
            request_str = request.decode('utf-8')
            
            # Check if it's a health check request
            if request_str.startswith('GET /health'):
                # Check NATS connection if client provided
                healthy = self.is_healthy
                
                if self.nats_client:
                    try:
                        # Verify NATS is connected
                        healthy = self.nats_client.nc.is_connected if hasattr(self.nats_client, 'nc') else True
                    except:
                        healthy = False
                
                if healthy:
                    response = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK\n"
                else:
                    response = b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nNATS Disconnected\n"
            else:
                # For any other request, return 404
                response = b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nNot Found\n"
            
            writer.write(response)
            await writer.drain()
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            try:
                writer.write(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
                await writer.drain()
            except:
                pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def start(self):
        """Start the health check server."""
        self.server = await asyncio.start_server(
            self.handle_request,
            '0.0.0.0',
            self.port
        )
        logger.info(f"Health check server running on port {self.port}")
    
    async def stop(self):
        """Stop the health check server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Health check server stopped")
    
    def mark_unhealthy(self):
        """Mark service as unhealthy."""
        self.is_healthy = False
    
    def mark_healthy(self):
        """Mark service as healthy."""
        self.is_healthy = True


async def run_health_check_server(port: int = 8080, nats_client = None):
    """
    Run health check server as a background task.
    
    Args:
        port: Port to listen on
        nats_client: Optional NATS client to monitor
    
    Returns:
        HealthCheckServer instance
    """
    server = HealthCheckServer(port, nats_client)
    await server.start()
    return server

