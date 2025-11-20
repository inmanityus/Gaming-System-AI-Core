"""
Improved end-to-end API integration tests with peer review fixes.
Tests complete workflows across multiple services with better reliability.
"""
import pytest
import asyncio
import aiohttp
from aiohttp import ClientTimeout
from datetime import datetime, timedelta, timezone
import numpy as np
import json
import sys
import os
import base64
import uuid
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@pytest.fixture(scope="session")
def base_url():
    """Get API base URL from environment or default."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
async def api_client():
    """Create API client with proper timeout configuration."""
    timeout = ClientTimeout(total=20, connect=5, sock_read=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        yield session


async def poll_for_db_record(
    conn,
    query: str,
    params: tuple,
    timeout_s: float = 15.0,
    poll_interval: float = 0.25
) -> Optional[Dict[str, Any]]:
    """
    Poll database for a record with exponential backoff.
    
    Args:
        conn: Database connection
        query: SQL query to execute
        params: Query parameters
        timeout_s: Maximum time to wait
        poll_interval: Initial polling interval
        
    Returns:
        Database record or None if timeout
    """
    deadline = asyncio.get_event_loop().time() + timeout_s
    interval = poll_interval
    last_error = None
    
    while asyncio.get_event_loop().time() < deadline:
        try:
            row = await conn.fetchrow(query, *params)
            if row:
                return dict(row)
        except Exception as e:
            last_error = e
        
        await asyncio.sleep(interval)
        # Exponential backoff with cap
        interval = min(interval * 1.5, 2.0)
    
    if last_error:
        raise Exception(f"Polling failed with error: {last_error}")
    
    return None


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.asyncio
class TestE2EAudioWorkflowImproved:
    """Improved E2E tests with better reliability and coverage."""
    
    async def _wait_for_service_ready(
        self,
        api_client: aiohttp.ClientSession,
        base_url: str,
        timeout: float = 30.0
    ) -> bool:
        """Wait for service to be ready with health check."""
        health_url = f"{base_url}/health"
        deadline = asyncio.get_event_loop().time() + timeout
        
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with api_client.get(health_url) as resp:
                    if resp.status == 200:
                        return True
            except aiohttp.ClientError:
                pass
            
            await asyncio.sleep(1.0)
        
        return False
    
    async def test_complete_audio_submission_workflow(
        self,
        postgres_pool,
        api_client,
        base_url,
        sample_audio_48khz
    ):
        """Test complete workflow with improved reliability."""
        # Wait for service to be ready
        if not await self._wait_for_service_ready(api_client, base_url):
            pytest.skip("API service not available")
        
        # Generate unique IDs to avoid collisions
        user_id = f"e2e_user_{uuid.uuid4().hex[:8]}"
        session_id = f"e2e_session_{uuid.uuid4().hex[:8]}"
        request_id = uuid.uuid4().hex
        
        # Prepare audio data
        audio_data, sample_rate = sample_audio_48khz
        # Ensure audio is properly clipped and converted
        audio_bytes = (audio_data.clip(-1, 1) * 32767).astype(np.int16).tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Request headers with correlation ID
        headers = {
            "X-Request-ID": request_id,
            "Content-Type": "application/json",
            # Add auth header if required
            # "Authorization": f"Bearer {api_token}"
        }
        
        # Prepare payload with all required fields
        payload = {
            "audio_data": audio_b64,
            "sample_rate": int(sample_rate),
            "user_id": user_id,
            "session_id": session_id,
            "encoding": "PCM_S16LE",
            "channels": 1,
            "duration_seconds": len(audio_data) / sample_rate
        }
        
        # Submit for analysis with proper error handling
        analyze_url = f"{base_url}/api/v1/audio/analyze"
        
        async with api_client.post(
            analyze_url,
            json=payload,
            headers=headers
        ) as resp:
            response_body = await resp.text()
            
            if resp.status != 200:
                pytest.fail(
                    f"POST {analyze_url} failed with status {resp.status}:\n"
                    f"Headers: {dict(resp.headers)}\n"
                    f"Body: {response_body}"
                )
            
            try:
                result = json.loads(response_body)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON response: {response_body}")
        
        # Validate response schema
        assert isinstance(result, dict), "Response must be a JSON object"
        
        # Check required fields
        required_fields = ["analysis_id", "intelligibility_score", "archetype_matches"]
        missing_fields = [f for f in required_fields if f not in result]
        assert not missing_fields, f"Missing required fields: {missing_fields}"
        
        # Validate field types and ranges
        analysis_id = result["analysis_id"]
        assert isinstance(analysis_id, str) and analysis_id, "analysis_id must be non-empty string"
        
        intelligibility_score = result["intelligibility_score"]
        assert isinstance(intelligibility_score, (int, float)), "intelligibility_score must be numeric"
        assert 0.0 <= intelligibility_score <= 1.0, f"intelligibility_score {intelligibility_score} out of range [0, 1]"
        
        archetype_matches = result["archetype_matches"]
        assert isinstance(archetype_matches, list), "archetype_matches must be a list"
        
        # Validate archetype match structure
        for i, match in enumerate(archetype_matches):
            assert isinstance(match, dict), f"archetype_matches[{i}] must be a dict"
            assert "name" in match, f"archetype_matches[{i}] missing 'name'"
            assert "score" in match, f"archetype_matches[{i}] missing 'score'"
            assert isinstance(match["score"], (int, float)), f"archetype_matches[{i}].score must be numeric"
            assert 0.0 <= match["score"] <= 1.0, f"archetype_matches[{i}].score out of range"
        
        # Verify optional fields if present
        if "confidence" in result:
            assert isinstance(result["confidence"], (int, float))
            assert 0.0 <= result["confidence"] <= 1.0
        
        if "processing_time_ms" in result:
            assert isinstance(result["processing_time_ms"], (int, float))
            assert result["processing_time_ms"] >= 0
        
        # Verify database persistence with polling
        async with postgres_pool.acquire() as conn:
            # Poll for the record using analysis_id
            query = """
                SELECT 
                    analysis_id,
                    user_id,
                    session_id,
                    sample_rate,
                    intelligibility_score,
                    archetype_matches,
                    confidence_level,
                    created_at
                FROM ethelred.audio_metrics
                WHERE analysis_id = $1
            """
            
            row = await poll_for_db_record(
                conn,
                query,
                (analysis_id,),
                timeout_s=20.0
            )
            
            assert row is not None, f"Timeout waiting for DB record with analysis_id={analysis_id}"
            
            # Validate database fields match API response
            assert row["analysis_id"] == analysis_id
            assert row["user_id"] == user_id
            assert row["session_id"] == session_id
            assert row["sample_rate"] == sample_rate
            
            # Allow small floating point differences
            assert abs(row["intelligibility_score"] - intelligibility_score) < 1e-6, \
                f"DB score {row['intelligibility_score']} != API score {intelligibility_score}"
            
            # Verify archetype matches if stored as JSON
            if row["archetype_matches"]:
                db_matches = json.loads(row["archetype_matches"])
                assert len(db_matches) == len(archetype_matches)
                for i, (db_match, api_match) in enumerate(zip(db_matches, archetype_matches)):
                    assert db_match["name"] == api_match["name"]
                    assert abs(db_match["score"] - api_match["score"]) < 1e-6
        
        # Test retrieval endpoint if available
        retrieve_url = f"{base_url}/api/v1/audio/analyses/{analysis_id}"
        try:
            async with api_client.get(
                retrieve_url,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    retrieved = await resp.json()
                    
                    # Validate retrieved data matches original
                    assert retrieved["analysis_id"] == analysis_id
                    assert retrieved["user_id"] == user_id
                    assert retrieved["session_id"] == session_id
                    assert abs(retrieved["intelligibility_score"] - intelligibility_score) < 1e-6
                elif resp.status == 404:
                    # Retrieval endpoint might not be implemented yet
                    pass
                else:
                    body = await resp.text()
                    pytest.fail(f"GET {retrieve_url} returned unexpected status {resp.status}: {body}")
        except aiohttp.ClientError:
            # Retrieval endpoint might not be available
            pass
        
        # Cleanup test data
        async with postgres_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM ethelred.audio_metrics WHERE analysis_id = $1",
                analysis_id
            )
    
    @pytest.mark.parametrize("sample_rate,duration", [
        (8000, 1),    # Low quality, short
        (48000, 3),   # High quality, medium
        (44100, 5),   # CD quality, longer
    ])
    async def test_audio_analysis_various_formats(
        self,
        postgres_pool,
        api_client,
        base_url,
        sample_rate: int,
        duration: int
    ):
        """Test audio analysis with various sample rates and durations."""
        if not await self._wait_for_service_ready(api_client, base_url):
            pytest.skip("API service not available")
        
        # Generate test audio
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        # Mix of frequencies for more realistic audio
        audio_data = (
            0.3 * np.sin(440 * 2 * np.pi * t) +  # A4
            0.2 * np.sin(554.37 * 2 * np.pi * t) +  # C#5
            0.1 * np.sin(659.25 * 2 * np.pi * t)  # E5
        )
        audio_data += 0.05 * np.random.normal(0, 1, samples)  # Add some noise
        audio_data = audio_data.clip(-1, 1)
        
        # Prepare request
        user_id = f"e2e_format_test_{uuid.uuid4().hex[:8]}"
        session_id = f"e2e_session_{uuid.uuid4().hex[:8]}"
        
        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        payload = {
            "audio_data": audio_b64,
            "sample_rate": sample_rate,
            "user_id": user_id,
            "session_id": session_id,
            "encoding": "PCM_S16LE",
            "channels": 1,
            "duration_seconds": duration
        }
        
        # Submit and verify
        async with api_client.post(
            f"{base_url}/api/v1/audio/analyze",
            json=payload,
            headers={"X-Request-ID": uuid.uuid4().hex}
        ) as resp:
            assert resp.status == 200, f"Failed for {sample_rate}Hz/{duration}s"
            result = await resp.json()
            
            # Basic validation
            assert "analysis_id" in result
            assert 0.0 <= result["intelligibility_score"] <= 1.0
            
            # Cleanup
            async with postgres_pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM ethelred.audio_metrics WHERE analysis_id = $1",
                    result["analysis_id"]
                )
    
    async def test_invalid_audio_submission_errors(
        self,
        api_client,
        base_url
    ):
        """Test API error handling for invalid submissions."""
        if not await self._wait_for_service_ready(api_client, base_url):
            pytest.skip("API service not available")
        
        analyze_url = f"{base_url}/api/v1/audio/analyze"
        headers = {"X-Request-ID": uuid.uuid4().hex}
        
        # Test cases for various invalid inputs
        test_cases = [
            {
                "name": "missing_audio_data",
                "payload": {
                    "sample_rate": 48000,
                    "user_id": "test",
                    "session_id": "test"
                },
                "expected_status": 400,
                "expected_error": "audio_data"
            },
            {
                "name": "invalid_base64",
                "payload": {
                    "audio_data": "not-valid-base64!!!",
                    "sample_rate": 48000,
                    "user_id": "test",
                    "session_id": "test"
                },
                "expected_status": 400,
                "expected_error": "base64"
            },
            {
                "name": "negative_sample_rate",
                "payload": {
                    "audio_data": base64.b64encode(b"test").decode(),
                    "sample_rate": -48000,
                    "user_id": "test",
                    "session_id": "test"
                },
                "expected_status": 400,
                "expected_error": "sample_rate"
            },
            {
                "name": "missing_user_id",
                "payload": {
                    "audio_data": base64.b64encode(b"test").decode(),
                    "sample_rate": 48000,
                    "session_id": "test"
                },
                "expected_status": 400,
                "expected_error": "user_id"
            },
            {
                "name": "oversized_payload",
                "payload": {
                    "audio_data": base64.b64encode(b"x" * 50_000_000).decode(),  # 50MB
                    "sample_rate": 48000,
                    "user_id": "test",
                    "session_id": "test"
                },
                "expected_status": 413,  # Payload too large
                "expected_error": "size"
            }
        ]
        
        for test_case in test_cases:
            async with api_client.post(
                analyze_url,
                json=test_case["payload"],
                headers=headers
            ) as resp:
                body = await resp.text()
                
                assert resp.status == test_case["expected_status"], (
                    f"Test '{test_case['name']}' expected status {test_case['expected_status']} "
                    f"but got {resp.status}. Body: {body}"
                )
                
                # Verify error message contains expected keyword
                assert test_case["expected_error"].lower() in body.lower(), (
                    f"Test '{test_case['name']}' expected error about '{test_case['expected_error']}' "
                    f"but got: {body}"
                )


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.asyncio
class TestE2EConcurrencyAndLoad:
    """Test concurrent requests and basic load scenarios."""
    
    async def test_concurrent_audio_submissions(
        self,
        postgres_pool,
        api_client,
        base_url,
        sample_audio_48khz
    ):
        """Test that concurrent submissions don't interfere with each other."""
        if not os.getenv("RUN_LOAD_TESTS"):
            pytest.skip("Set RUN_LOAD_TESTS=1 to run load tests")
        
        # Prepare 10 different users submitting simultaneously
        audio_data, sample_rate = sample_audio_48khz
        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        tasks = []
        expected_results = []
        
        for i in range(10):
            user_id = f"concurrent_user_{i}_{uuid.uuid4().hex[:8]}"
            session_id = f"concurrent_session_{i}_{uuid.uuid4().hex[:8]}"
            
            payload = {
                "audio_data": audio_b64,
                "sample_rate": sample_rate,
                "user_id": user_id,
                "session_id": session_id,
                "encoding": "PCM_S16LE",
                "channels": 1
            }
            
            expected_results.append({
                "user_id": user_id,
                "session_id": session_id
            })
            
            # Create task but don't await yet
            task = api_client.post(
                f"{base_url}/api/v1/audio/analyze",
                json=payload,
                headers={"X-Request-ID": f"concurrent_{i}_{uuid.uuid4().hex}"}
            )
            tasks.append(task)
        
        # Submit all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        analysis_ids = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                pytest.fail(f"Request {i} failed with exception: {response}")
            
            async with response as resp:
                assert resp.status == 200, f"Request {i} failed with status {resp.status}"
                result = await resp.json()
                analysis_ids.append(result["analysis_id"])
        
        # Verify all records in database are distinct
        async with postgres_pool.acquire() as conn:
            records = await conn.fetch("""
                SELECT analysis_id, user_id, session_id
                FROM ethelred.audio_metrics
                WHERE analysis_id = ANY($1)
            """, analysis_ids)
            
            assert len(records) == len(analysis_ids), "Some records missing from database"
            
            # Verify no cross-contamination
            for record in records:
                matching = [e for e in expected_results 
                          if e["user_id"] == record["user_id"]]
                assert len(matching) == 1, f"User ID contamination for {record['user_id']}"
                assert matching[0]["session_id"] == record["session_id"]
            
            # Cleanup
            await conn.execute(
                "DELETE FROM ethelred.audio_metrics WHERE analysis_id = ANY($1)",
                analysis_ids
            )
