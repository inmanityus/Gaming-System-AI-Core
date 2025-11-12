"""
Main entry point for Language System gRPC server
"""

import asyncio
import logging
import signal
import sys
from language_system.grpc.grpc_server import LanguageSystemGRPCServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main server function"""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 50051
    server = LanguageSystemGRPCServer(port=port)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        asyncio.create_task(server.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await server.start()
        logger.info(f"Language System gRPC server running on port {port}")
        await server.wait_for_termination()
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())

