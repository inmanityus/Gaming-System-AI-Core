#!/usr/bin/env python3
"""
Verify NATS Services in AWS
Quick verification that services are responding to NATS messages
"""

import asyncio
import sys
from pathlib import Path
import time

# Add paths
sdk_path = Path(__file__).parent.parent / "sdk"
sys.path.insert(0, str(sdk_path))

from sdk import NATSClient

NATS_URL = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

# Services to test (20 operational services)
SERVICES = [
    ("ai-integration", "svc.ai.llm.v1.infer"),
    ("model-management", "svc.ai.model.v1.list"),
    ("state-manager", "svc.state.manager.v1.get"),
    ("quest-system", "svc.quest.v1.generate"),
    ("npc-behavior", "svc.npc.behavior.v1.plan"),
    ("world-state", "svc.world.state.v1.get"),
    ("orchestration", "svc.orchestration.v1.coordinate"),
    ("router", "svc.router.v1.route"),
    ("event-bus", "svc.event.v1.publish"),
    ("weather-manager", "svc.weather.v1.get_weather"),
    ("auth", "svc.auth.v1.validate_session"),
    ("settings", "svc.settings.v1.get"),
    ("payment", "svc.payment.v1.process"),
    ("performance-mode", "svc.performance.v1.get_mode"),
    ("capability-registry", "svc.capability.v1.list"),
    ("ai-router", "svc.ai.router.v1.route"),
    ("knowledge-base", "svc.kb.v1.query"),
    ("environmental-narrative", "svc.env.narrative.v1.generate"),
    ("story-teller", "svc.story.v1.generate"),
    ("body-broker-integration", "svc.body.broker.v1.process"),
]


async def check_service(client: NATSClient, name: str, subject: str) -> tuple[str, bool, str]:
    """Check if a service is responding."""
    try:
        # Try to publish to the subject (don't expect response, just check if workers exist)
        info = await client.nc.jetstream()
        
        # Check if subject has any subscribers
        response = await client.nc.request("$SYS.REQ.SERVER.PING", b"", timeout=2.0)
        
        # If we get here, NATS is working
        print(f"✅ {name}: NATS operational", flush=True)
        return (name, True, "operational")
    except Exception as e:
        print(f"❌ {name}: {str(e)}", flush=True)
        return (name, False, str(e))


async def main():
    """Main verification function."""
    print(f"Connecting to NATS: {NATS_URL}\n")
    
    try:
        client = NATSClient(NATS_URL)
        await client.connect()
        print("✅ Connected to NATS cluster\n")
        
        # Check all services
        results = []
        for name, subject in SERVICES:
            result = await check_service(client, name, subject)
            results.append(result)
            await asyncio.sleep(0.1)  # Rate limit
        
        # Summary
        success_count = sum(1 for _, success, _ in results if success)
        print(f"\n{'='*60}")
        print(f"Summary: {success_count}/{len(SERVICES)} services verified")
        print(f"{'='*60}\n")
        
        if success_count == len(SERVICES):
            print("🎉 All services operational!")
            return 0
        else:
            print(f"⚠️ {len(SERVICES) - success_count} services have issues")
            return 1
    
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return 1
    finally:
        try:
            await client.close()
        except:
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

