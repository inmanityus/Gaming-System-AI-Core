"""
Client library for Token Window Management System.
Easy integration for existing services.
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Union
import json
import logging


logger = logging.getLogger(__name__)


class TokenManagementClient:
    """Client for interacting with Token Window Management System."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def create_completion(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True
    ) -> Union[Dict, AsyncGenerator[str, None]]:
        """
        Create a completion with automatic token management.
        
        Args:
            session_id: Unique session identifier
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max output tokens (auto-calculated if not provided)
            stream: Whether to stream the response
            
        Returns:
            Dict for non-streaming or AsyncGenerator for streaming
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "session_id": session_id,
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        if stream:
            return self._stream_response(url, payload)
        else:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"API error: {response.status} - {error}")
                return await response.json()
    
    async def _stream_response(self, url: str, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream response from API."""
        async with self.session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"API error: {response.status} - {error}")
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if not line or line == "data: [DONE]":
                    continue
                
                if line.startswith("data: "):
                    line = line[6:]
                    
                try:
                    data = json.loads(line)
                    if "content" in data:
                        yield data["content"]
                    elif "error" in data:
                        raise Exception(f"Stream error: {data['error']}")
                except json.JSONDecodeError:
                    continue
    
    async def count_tokens(
        self,
        text: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = "gpt-4"
    ) -> Dict:
        """
        Count tokens for text or messages.
        
        Args:
            text: Text string to count
            messages: List of messages to count
            model: Model for tokenization
            
        Returns:
            Dict with token count and context info
        """
        url = f"{self.base_url}/tokens/count"
        
        payload = {"model": model}
        if text:
            payload["text"] = text
        elif messages:
            payload["messages"] = messages
        else:
            raise ValueError("Either text or messages must be provided")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"API error: {response.status} - {error}")
            return await response.json()
    
    async def get_session_info(self, session_id: str) -> Dict:
        """Get information about a session."""
        url = f"{self.base_url}/sessions/{session_id}"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.get(url) as response:
            if response.status == 404:
                return None
            elif response.status != 200:
                error = await response.text()
                raise Exception(f"API error: {response.status} - {error}")
            return await response.json()
    
    async def list_sessions(self) -> Dict:
        """List all active sessions."""
        url = f"{self.base_url}/sessions"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.get(url) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"API error: {response.status} - {error}")
            return await response.json()
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        url = f"{self.base_url}/sessions/{session_id}"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.delete(url) as response:
            return response.status == 200
    
    async def get_metrics(self) -> Dict:
        """Get system metrics."""
        url = f"{self.base_url}/metrics"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.get(url) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"API error: {response.status} - {error}")
            return await response.json()
    
    async def list_models(self) -> Dict:
        """List available models and their capabilities."""
        url = f"{self.base_url}/models"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.get(url) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"API error: {response.status} - {error}")
            return await response.json()


# Example usage
async def example_usage():
    """Example of using the token management client."""
    
    async with TokenManagementClient() as client:
        # Start a conversation
        session_id = "user_123_session_456"
        
        messages = [
            {"role": "system", "content": "You are a helpful gaming assistant."},
            {"role": "user", "content": "Tell me about the best strategies for RPG games."}
        ]
        
        # Stream a response
        print("Streaming response:")
        async for chunk in await client.create_completion(
            session_id=session_id,
            messages=messages,
            model="gpt-4o",
            stream=True
        ):
            print(chunk, end="", flush=True)
        print("\n")
        
        # Check session info
        session_info = await client.get_session_info(session_id)
        print(f"\nSession info: {json.dumps(session_info, indent=2)}")
        
        # Count tokens
        token_info = await client.count_tokens(
            messages=messages,
            model="gpt-4o"
        )
        print(f"\nToken count: {json.dumps(token_info, indent=2)}")
        
        # List models
        models = await client.list_models()
        print(f"\nAvailable models: {json.dumps(models, indent=2)}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
