"""Benchmark all Body Broker systems for performance validation"""
import asyncio
import time
from services.harvesting.body_part_extraction import HarvestingSystem, ExtractionMethod, ToolQuality, BodyPartType
from services.negotiation.haggling_system import HagglingSystem, NegotiationContext, ClientTemperament


async def benchmark_harvesting(iterations=100):
    """Benchmark harvesting system."""
    system = HarvestingSystem()
    
    start = time.time()
    for i in range(iterations):
        await system.extract_parts(
            f"target_{i}",
            ExtractionMethod.BLADE_KILL,
            ToolQuality.STANDARD,
            [BodyPartType.KIDNEY],
            0.6
        )
    elapsed = time.time() - start
    
    print(f"Harvesting: {iterations} extractions in {elapsed:.2f}s ({iterations/elapsed:.1f}/sec)")


async def benchmark_negotiation(iterations=100):
    """Benchmark negotiation system."""
    system = HagglingSystem()
    
    context = NegotiationContext(
        "client_001", "Test", ClientTemperament.AGGRESSIVE,
        "low", "good", 10000.0, 50, 5, "normal"
    )
    
    start = time.time()
    for i in range(iterations):
        await system.negotiate_deal(context, ["appeal_to_greed"])
    elapsed = time.time() - start
    
    print(f"Negotiation: {iterations} deals in {elapsed:.2f}s ({iterations/elapsed:.1f}/sec)")


async def main():
    print("Body Broker Performance Benchmarks\n")
    await benchmark_harvesting(100)
    await benchmark_negotiation(100)


if __name__ == "__main__":
    asyncio.run(main())

