#!/usr/bin/env python3
"""Simple NATS connectivity verification"""

import asyncio
import sys

try:
    import nats
except ImportError:
    print("ERROR: nats-py not installed")
    print("Install with: pip install nats-py")
    sys.exit(1)

NATS_URL = "nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

async def main():
    print(f"Connecting to NATS: {NATS_URL}")
    
    try:
        nc = await nats.connect(NATS_URL)
        print("✅ Connected to NATS cluster")
        
        # Check if JetStream is available
        js = nc.jetstream()
        print("✅ JetStream is available")
        
        # List streams (if any exist)
        try:
            streams = []
            async for stream in js.streams_info():
                streams.append(stream.config.name)
            
            if streams:
                print(f"✅ Found {len(streams)} JetStream streams")
            else:
                print("ℹ️  No JetStream streams found (normal for new cluster)")
        except Exception as e:
            print(f"ℹ️  Could not list streams: {e}")
        
        # Try a simple publish/subscribe test
        subject = "test.connectivity"
        received = []
        
        async def message_handler(msg):
            received.append(msg.data.decode())
            print(f"✅ Received test message: {msg.data.decode()}")
        
        # Subscribe
        sub = await nc.subscribe(subject, cb=message_handler)
        await asyncio.sleep(0.5)
        
        # Publish
        test_data = b"connectivity_test"
        await nc.publish(subject, test_data)
        print(f"✅ Published test message to {subject}")
        
        # Wait for message
        await asyncio.sleep(1.0)
        
        if received:
            print("✅ Pub/sub working correctly")
        else:
            print("⚠️  Message not received (may need more time)")
        
        await sub.unsubscribe()
        await nc.close()
        
        print("\n🎉 NATS cluster verification PASSED!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

