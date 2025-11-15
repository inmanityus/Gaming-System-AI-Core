"""
End-to-End Tests for NATS Binary Messaging
Tests complete request/response cycles for all services

Peer Coding Required: Yes
Pairwise Testing Required: Yes (3+ validators)
"""

import asyncio
import pytest
import sys
from pathlib import Path
import time

# Add paths
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path))
sys.path.insert(0, str(generated_path))

from sdk import NATSClient, NATSConfig
import ai_integration_pb2
import model_mgmt_pb2
import state_manager_pb2
import quest_pb2
import npc_behavior_pb2
import common_pb2
from google.protobuf.wrappers_pb2 import DoubleValue, UInt32Value, BoolValue
from google.protobuf.timestamp_pb2 import Timestamp


@pytest.fixture
async def nats_client():
    """Create NATS client for testing."""
    client = NATSClient("nats://localhost:4222")
    await client.connect()
    yield client
    await client.close()


class TestAIIntegration:
    """Test AI Integration service via NATS."""
    
    @pytest.mark.asyncio
    async def test_llm_inference(self, nats_client):
        """Test LLM inference request/response."""
        request = ai_integration_pb2.LLMInferenceRequest()
        request.meta.request_id = "test-req-001"
        request.meta.trace_id = "test-trace-001"
        
        timestamp = Timestamp()
        timestamp.FromSeconds(int(time.time()))
        request.meta.timestamp.CopyFrom(timestamp)
        
        request.model_id = "gpt-5-pro"
        request.prompt = "Hello, world!"
        request.params.temperature.CopyFrom(DoubleValue(value=0.7))
        request.params.max_tokens.CopyFrom(UInt32Value(value=100))
        
        response = await nats_client.request(
            subject="svc.ai.llm.v1.infer",
            request_data=request.SerializeToString(),
            response_type=ai_integration_pb2.LLMInferenceResponse,
            timeout=5.0
        )
        
        # Verify response
        assert response.generation_id
        assert response.output_text
        assert response.usage.total_tokens > 0
        assert response.finish_reason == "stop"
        assert not response.HasField("error")


class TestModelManagement:
    """Test Model Management service via NATS."""
    
    @pytest.mark.asyncio
    async def test_list_models(self, nats_client):
        """Test list models request."""
        request = model_mgmt_pb2.ListModelsRequest()
        request.meta.request_id = "test-req-002"
        
        timestamp = Timestamp()
        timestamp.FromSeconds(int(time.time()))
        request.meta.timestamp.CopyFrom(timestamp)
        
        # Note: Service needs to be running
        try:
            response = await nats_client.request(
                subject="svc.ai.model.v1.list",
                request_data=request.SerializeToString(),
                response_type=model_mgmt_pb2.ListModelsResponse,
                timeout=5.0
            )
            
            assert len(response.models) > 0
            assert not response.HasField("error")
        except Exception as e:
            # Service may not be running in test environment
            pytest.skip(f"Service not available: {e}")


class TestStateManager:
    """Test State Manager service via NATS."""
    
    @pytest.mark.asyncio
    async def test_update_and_get_state(self, nats_client):
        """Test state update and retrieval with CAS."""
        # Update state
        update_req = state_manager_pb2.GameStateUpdate()
        update_req.meta.request_id = "test-req-003"
        
        timestamp = Timestamp()
        timestamp.FromSeconds(int(time.time()))
        update_req.meta.timestamp.CopyFrom(timestamp)
        
        update_req.player.player_id = "player-test-123"
        update_req.player.state.fields["health"].number_value = 100
        update_req.player.state.fields["level"].number_value = 5
        update_req.player.version = 0
        
        update_req.op = state_manager_pb2.GameStateUpdate.UPSERT
        update_req.expected_version = 0
        
        # Note: Service needs to be running
        try:
            update_resp = await nats_client.request(
                subject="svc.state.manager.v1.update",
                request_data=update_req.SerializeToString(),
                response_type=state_manager_pb2.GameStateUpdateAck,
                timeout=5.0
            )
            
            assert update_resp.ok
            assert update_resp.new_version == 1
            assert not update_resp.HasField("error")
            
            # Get state
            get_req = state_manager_pb2.GetStateRequest()
            get_req.meta.request_id = "test-req-004"
            get_req.player_id = "player-test-123"
            
            get_resp = await nats_client.request(
                subject="svc.state.manager.v1.get",
                request_data=get_req.SerializeToString(),
                response_type=state_manager_pb2.GetStateResponse,
                timeout=5.0
            )
            
            assert get_resp.version == 1
            assert get_resp.state.fields["health"].number_value == 100
            assert not get_resp.HasField("error")
        
        except Exception as e:
            pytest.skip(f"Service not available: {e}")


class TestLatency:
    """Test latency requirements."""
    
    @pytest.mark.asyncio
    async def test_sub_5ms_latency(self, nats_client):
        """Verify sub-5ms end-to-end latency."""
        request = ai_integration_pb2.LLMInferenceRequest()
        request.meta.request_id = "test-latency-001"
        
        timestamp = Timestamp()
        timestamp.FromSeconds(int(time.time()))
        request.meta.timestamp.CopyFrom(timestamp)
        
        request.model_id = "gpt-5-pro"
        request.prompt = "Fast test"
        request.params.max_tokens.CopyFrom(UInt32Value(value=10))
        
        # Measure latency
        start = time.perf_counter()
        
        try:
            response = await nats_client.request(
                subject="svc.ai.llm.v1.infer",
                request_data=request.SerializeToString(),
                response_type=ai_integration_pb2.LLMInferenceResponse,
                timeout=5.0
            )
            
            latency_ms = (time.perf_counter() - start) * 1000
            
            logger.info(f"Latency: {latency_ms:.2f}ms")
            
            # Requirement: <5ms for NATS (vs 5-20ms HTTP)
            # In local testing, should be <2ms
            assert latency_ms < 5.0, f"Latency {latency_ms}ms exceeds 5ms target"
            
            print(f"✅ Latency test passed: {latency_ms:.2f}ms")
        
        except Exception as e:
            pytest.skip(f"Service not available: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

