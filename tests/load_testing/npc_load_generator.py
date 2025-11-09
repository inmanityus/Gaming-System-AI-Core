"""
NPC Load Generator for Load Testing
Simulates realistic NPC interactions at scale to validate system performance.

Test Scenarios:
- Scenario 1: Baseline (100 NPCs)
- Scenario 2: Medium (1,000 NPCs)
- Scenario 3: High (10,000 NPCs)
- Scenario 4: Spike (100 → 5,000 in 5 minutes)
- Scenario 5: Sustained (1,000 NPCs for 4 hours)
- Scenario 6: Failure Recovery (kill instances mid-test)
"""

import asyncio
import aiohttp
import time
import random
import logging
from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class NPCSimulator:
    """Simulates single NPC with realistic behavior patterns."""
    
    npc_id: str
    archetype: str
    personality_traits: Dict
    interaction_rate: float  # Actions per minute
    active: bool = True
    total_interactions: int = 0
    errors: int = 0
    latencies: List[float] = field(default_factory=list)
    
    async def simulate_interaction(self, session: aiohttp.ClientSession, endpoint: str):
        """Simulate one NPC interaction with the backend."""
        if not self.active:
            return
        
        start_time = time.time()
        
        try:
            # Simulate NPC action request
            payload = {
                "npc_id": self.npc_id,
                "archetype": self.archetype,
                "action": random.choice(["speak", "move", "emote", "interact"]),
                "context": {
                    "personality": self.personality_traits,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            async with session.post(
                f"{endpoint}/api/npc/action",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as response:
                await response.read()
                
                latency = (time.time() - start_time) * 1000  # ms
                self.latencies.append(latency)
                self.total_interactions += 1
                
                if response.status != 200:
                    self.errors += 1
                    logger.warning(f"NPC {self.npc_id}: HTTP {response.status}")
        
        except asyncio.TimeoutError:
            self.errors += 1
            latency = (time.time() - start_time) * 1000
            self.latencies.append(latency)
            logger.warning(f"NPC {self.npc_id}: Timeout after {latency:.0f}ms")
        
        except Exception as e:
            self.errors += 1
            logger.error(f"NPC {self.npc_id}: Error - {e}")
    
    async def run_simulation(self, session: aiohttp.ClientSession, endpoint: str, duration_seconds: int):
        """Run continuous NPC simulation for specified duration."""
        end_time = time.time() + duration_seconds
        
        while self.active and time.time() < end_time:
            # Simulate interaction
            await self.simulate_interaction(session, endpoint)
            
            # Wait until next interaction (based on interaction rate)
            wait_time = 60.0 / self.interaction_rate  # Convert rate to seconds
            await asyncio.sleep(wait_time + random.uniform(-0.5, 0.5))


class LoadTestOrchestrator:
    """Orchestrates load testing scenarios with multiple NPCs."""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.npcs: List[NPCSimulator] = []
        self.start_time = None
        self.end_time = None
    
    def create_npc_pool(self, count: int, archetype_distribution: Dict[str, float] = None):
        """Create pool of simulated NPCs with realistic distribution."""
        if archetype_distribution is None:
            # Default distribution
            archetype_distribution = {
                "vampire": 0.15,
                "werewolf": 0.15,
                "zombie": 0.40,
                "ghoul": 0.15,
                "lich": 0.05,
                "human": 0.10
            }
        
        logger.info(f"Creating {count} NPCs with archetype distribution...")
        
        self.npcs = []
        for i in range(count):
            # Select archetype based on distribution
            rand = random.random()
            cumulative = 0
            archetype = "human"
            
            for arch, prob in archetype_distribution.items():
                cumulative += prob
                if rand <= cumulative:
                    archetype = arch
                    break
            
            # Create NPC with random personality
            npc = NPCSimulator(
                npc_id=str(uuid.uuid4()),
                archetype=archetype,
                personality_traits={
                    "aggression": random.uniform(0, 1),
                    "sociability": random.uniform(0, 1),
                    "intelligence": random.uniform(0, 1)
                },
                interaction_rate=random.uniform(0.5, 2.0)  # 0.5-2 actions per minute
            )
            self.npcs.append(npc)
        
        logger.info(f"✅ Created {len(self.npcs)} NPCs")
    
    async def run_scenario(
        self,
        npc_count: int,
        duration_minutes: int,
        ramp_up_minutes: int = 0
    ):
        """
        Run load test scenario.
        
        Args:
            npc_count: Number of concurrent NPCs
            duration_minutes: Test duration after ramp-up
            ramp_up_minutes: Time to gradually add NPCs (0 = immediate)
        """
        logger.info("=" * 70)
        logger.info(f"LOAD TEST SCENARIO")
        logger.info("=" * 70)
        logger.info(f"NPCs: {npc_count}")
        logger.info(f"Duration: {duration_minutes} minutes")
        logger.info(f"Ramp-up: {ramp_up_minutes} minutes")
        logger.info(f"Endpoint: {self.endpoint}")
        logger.info("=" * 70)
        
        # Create NPC pool
        self.create_npc_pool(npc_count)
        
        self.start_time = time.time()
        
        # Create aiohttp session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=500,  # Max concurrent connections
            limit_per_host=100
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            if ramp_up_minutes > 0:
                # Gradual ramp-up
                logger.info(f"🚀 Starting gradual ramp-up over {ramp_up_minutes} minutes...")
                await self._ramp_up(session, duration_minutes, ramp_up_minutes)
            else:
                # Immediate full load
                logger.info(f"🚀 Starting immediate full load ({npc_count} NPCs)...")
                tasks = [
                    npc.run_simulation(session, self.endpoint, duration_minutes * 60)
                    for npc in self.npcs
                ]
                await asyncio.gather(*tasks)
        
        self.end_time = time.time()
        
        # Generate report
        self._generate_report()
    
    async def _ramp_up(self, session: aiohttp.ClientSession, test_duration: int, ramp_duration: int):
        """Gradually ramp up NPCs over specified time."""
        npcs_per_wave = max(1, len(self.npcs) // (ramp_duration * 4))  # 4 waves per minute
        wave_interval = (ramp_duration * 60) / (len(self.npcs) // npcs_per_wave)
        
        active_tasks = []
        
        for i in range(0, len(self.npcs), npcs_per_wave):
            wave = self.npcs[i:i + npcs_per_wave]
            logger.info(f"  Wave {i//npcs_per_wave + 1}: Adding {len(wave)} NPCs (total active: {i + len(wave)})")
            
            for npc in wave:
                task = asyncio.create_task(
                    npc.run_simulation(session, self.endpoint, test_duration * 60)
                )
                active_tasks.append(task)
            
            await asyncio.sleep(wave_interval)
        
        # Wait for all tasks to complete
        await asyncio.gather(*active_tasks)
    
    def _generate_report(self):
        """Generate performance report from test results."""
        duration = self.end_time - self.start_time
        
        # Collect all latencies
        all_latencies = []
        total_interactions = 0
        total_errors = 0
        
        for npc in self.npcs:
            all_latencies.extend(npc.latencies)
            total_interactions += npc.total_interactions
            total_errors += npc.errors
        
        if not all_latencies:
            logger.error("❌ No successful interactions recorded")
            return
        
        # Sort for percentile calculation
        all_latencies.sort()
        
        # Calculate percentiles
        p50_idx = int(len(all_latencies) * 0.50)
        p95_idx = int(len(all_latencies) * 0.95)
        p99_idx = int(len(all_latencies) * 0.99)
        
        p50 = all_latencies[p50_idx]
        p95 = all_latencies[p95_idx]
        p99 = all_latencies[p99_idx]
        avg = sum(all_latencies) / len(all_latencies)
        
        # Calculate rates
        interactions_per_sec = total_interactions / duration if duration > 0 else 0
        error_rate = (total_errors / total_interactions * 100) if total_interactions > 0 else 0
        
        # Print report
        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 LOAD TEST RESULTS")
        logger.info("=" * 70)
        logger.info(f"Test Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logger.info(f"Concurrent NPCs: {len(self.npcs)}")
        logger.info(f"Total Interactions: {total_interactions}")
        logger.info(f"Interaction Rate: {interactions_per_sec:.1f}/sec")
        logger.info(f"Total Errors: {total_errors}")
        logger.info(f"Error Rate: {error_rate:.2f}%")
        logger.info("")
        logger.info("Latency Percentiles:")
        logger.info(f"  P50: {p50:.1f}ms")
        logger.info(f"  P95: {p95:.1f}ms")
        logger.info(f"  P99: {p99:.1f}ms")
        logger.info(f"  AVG: {avg:.1f}ms")
        logger.info("=" * 70)
        
        # Success criteria check
        success = True
        
        if error_rate > 1.0:
            logger.error(f"❌ FAIL: Error rate {error_rate:.2f}% exceeds 1% threshold")
            success = False
        
        if p95 > 500:
            logger.error(f"❌ FAIL: P95 latency {p95:.1f}ms exceeds 500ms threshold")
            success = False
        
        if p99 > 1000:
            logger.warning(f"⚠️ WARN: P99 latency {p99:.1f}ms exceeds 1000ms threshold")
        
        if success:
            logger.info("✅ PASS: All success criteria met")
        else:
            logger.error("❌ FAIL: Test did not meet success criteria")


# Scenario definitions
class LoadTestScenarios:
    """Predefined load test scenarios."""
    
    @staticmethod
    async def scenario_1_baseline():
        """Scenario 1: Baseline (100 NPCs, 10 minutes)"""
        orchestrator = LoadTestOrchestrator("http://localhost:8080")  # Update with actual endpoint
        await orchestrator.run_scenario(
            npc_count=100,
            duration_minutes=10,
            ramp_up_minutes=1
        )
    
    @staticmethod
    async def scenario_2_medium():
        """Scenario 2: Medium Scale (1,000 NPCs, 15 minutes)"""
        orchestrator = LoadTestOrchestrator("http://localhost:8080")
        await orchestrator.run_scenario(
            npc_count=1000,
            duration_minutes=15,
            ramp_up_minutes=3
        )
    
    @staticmethod
    async def scenario_3_high():
        """Scenario 3: High Scale (10,000 NPCs, 20 minutes)"""
        orchestrator = LoadTestOrchestrator("http://localhost:8080")
        await orchestrator.run_scenario(
            npc_count=10000,
            duration_minutes=20,
            ramp_up_minutes=10
        )
    
    @staticmethod
    async def scenario_4_spike():
        """Scenario 4: Spike Test (100 → 5,000 in 5 minutes)"""
        orchestrator = LoadTestOrchestrator("http://localhost:8080")
        await orchestrator.run_scenario(
            npc_count=5000,
            duration_minutes=10,
            ramp_up_minutes=5
        )
    
    @staticmethod
    async def scenario_5_sustained():
        """Scenario 5: Sustained Load (1,000 NPCs for 4 hours)"""
        orchestrator = LoadTestOrchestrator("http://localhost:8080")
        await orchestrator.run_scenario(
            npc_count=1000,
            duration_minutes=240,  # 4 hours
            ramp_up_minutes=5
        )


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python npc_load_generator.py <scenario>")
        print("Scenarios: baseline, medium, high, spike, sustained")
        sys.exit(1)
    
    scenario = sys.argv[1].lower()
    
    scenarios = {
        "baseline": LoadTestScenarios.scenario_1_baseline,
        "medium": LoadTestScenarios.scenario_2_medium,
        "high": LoadTestScenarios.scenario_3_high,
        "spike": LoadTestScenarios.scenario_4_spike,
        "sustained": LoadTestScenarios.scenario_5_sustained
    }
    
    if scenario not in scenarios:
        print(f"Unknown scenario: {scenario}")
        print(f"Available: {', '.join(scenarios.keys())}")
        sys.exit(1)
    
    logger.info(f"Running scenario: {scenario}")
    asyncio.run(scenarios[scenario]())

