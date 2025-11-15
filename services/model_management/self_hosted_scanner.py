"""
Self-Hosted Model Scanner - Scans downloadable models from HuggingFace, Ollama, etc.
Automatically identifies best downloadable models for different use cases.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import aiohttp
from aiohttp import ClientSession, ClientTimeout


class SelfHostedScanner:
    """
    Scans and ranks downloadable models from various sources.
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.timeout = ClientTimeout(total=60.0)  # Longer timeout for model downloads
        self.huggingface_token: Optional[str] = None  # Should come from config
    
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def scan_and_rank_models(
        self,
        use_case: str,
        sources: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan sources and rank models by suitability.
        
        Args:
            use_case: Use case identifier
            sources: List of sources to scan (huggingface, ollama, etc.)
        
        Returns:
            Ranked list of models
        """
        if sources is None:
            sources = ["huggingface", "ollama"]
        
        all_models = []
        
        for source in sources:
            try:
                if source == "huggingface":
                    models = await self._scan_huggingface(use_case)
                elif source == "ollama":
                    models = await self._scan_ollama(use_case)
                else:
                    continue
                
                all_models.extend(models)
            except Exception as e:
                print(f"Error scanning {source}: {e}")
                continue
        
        # Rank models
        ranked = await self._rank_models(all_models, use_case)
        
        return ranked
    
    async def _scan_huggingface(
        self,
        use_case: str
    ) -> List[Dict[str, Any]]:
        """
        Scan HuggingFace Hub for available models.
        
        Focuses on:
        - Instruction-tuned models
        - Chat models
        - Models suitable for use case
        """
        session = await self._get_session()
        models = []
        
        try:
            # Search for relevant models
            search_query = self._get_huggingface_search_query(use_case)
            
            headers = {}
            if self.huggingface_token:
                headers["Authorization"] = f"Bearer {self.huggingface_token}"
            
            async with session.get(
                f"https://huggingface.co/api/models",
                params={
                    "search": search_query,
                    "sort": "downloads",
                    "direction": -1,
                    "limit": 50
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for model_info in data:
                        # Get detailed model info
                        model_id = model_info.get("id")
                        model_details = await self._get_huggingface_model_details(model_id, session, headers)
                        
                        if model_details:
                            models.append({
                                "model_id": model_id,
                                "model_name": model_info.get("id"),
                                "provider": "huggingface",
                                "model_type": "self_hosted",
                                "use_case": use_case,
                                "downloads": model_info.get("downloads", 0),
                                "likes": model_info.get("likes", 0),
                                "tags": model_info.get("tags", []),
                                "pipeline_tag": model_info.get("pipeline_tag"),
                                **model_details
                            })
        except Exception as e:
            print(f"Error scanning HuggingFace: {e}")
        
        return models
    
    async def _scan_ollama(
        self,
        use_case: str
    ) -> List[Dict[str, Any]]:
        """
        Scan Ollama for available models.
        
        Ollama provides local model serving.
        """
        models = []
        
        # Known Ollama models that are good for different use cases
        ollama_models = [
            {
                "model_id": "llama3.1:8b",
                "model_name": "Llama 3.1 8B",
                "provider": "ollama",
                "model_type": "self_hosted",
                "use_case": use_case,
                "size": "4.7GB",
                "context_length": 128000,
                "quantization": "Q4_K_M"
            },
            {
                "model_id": "mistral:7b",
                "model_name": "Mistral 7B",
                "provider": "ollama",
                "model_type": "self_hosted",
                "use_case": use_case,
                "size": "4.1GB",
                "context_length": 32768,
                "quantization": "Q4_K_M"
            },
            {
                "model_id": "phi3:mini",
                "model_name": "Phi-3 Mini",
                "provider": "ollama",
                "model_type": "self_hosted",
                "use_case": use_case,
                "size": "2.2GB",
                "context_length": 128000,
                "quantization": "Q4_K_M"
            }
        ]
        
        # Filter by use case
        filtered = [
            m for m in ollama_models
            if self._is_ollama_model_suitable(m, use_case)
        ]
        
        return filtered
    
    async def _rank_models(
        self,
        models: List[Dict[str, Any]],
        use_case: str
    ) -> List[Dict[str, Any]]:
        """
        Rank models by suitability for use case.
        
        Ranking criteria:
        - Benchmark scores (40%)
        - Resource efficiency (20%)
        - Model size (10%)
        - Community health (15%)
        - Recent updates (15%)
        """
        ranked_models = []
        
        for model in models:
            score = 0.0
            
            # Benchmark scores (40%)
            benchmark_score = model.get("benchmark_score", 0.5)  # Default to neutral
            score += benchmark_score * 0.4
            
            # Resource efficiency (20%)
            efficiency = self._calculate_resource_efficiency(model)
            score += efficiency * 0.2
            
            # Model size (10% - smaller is better for our use case)
            size_score = self._calculate_size_score(model)
            score += size_score * 0.1
            
            # Community health (15%)
            community_score = self._calculate_community_score(model)
            score += community_score * 0.15
            
            # Recent updates (15%)
            update_score = self._calculate_update_score(model)
            score += update_score * 0.15
            
            model["rank_score"] = score
            ranked_models.append(model)
        
        # Sort by rank score (descending)
        ranked_models.sort(key=lambda x: x.get("rank_score", 0), reverse=True)
        
        return ranked_models
    
    def _get_huggingface_search_query(self, use_case: str) -> str:
        """Get search query for HuggingFace based on use case."""
        queries = {
            "story_generation": "instruct text-generation",
            "npc_dialogue": "chat conversational",
            "faction_decision": "instruct reasoning",
            "personality_model": "chat personality"
        }
        return queries.get(use_case, "instruct")
    
    async def _get_huggingface_model_details(
        self,
        model_id: str,
        session: ClientSession,
        headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a HuggingFace model."""
        try:
            async with session.get(
                f"https://huggingface.co/api/models/{model_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "model_card": data.get("model_card", ""),
                        "config": data.get("config", {}),
                        "siblings": data.get("siblings", [])
                    }
        except Exception as e:
            print(f"Error getting model details for {model_id}: {e}")
        
        return None
    
    def _is_ollama_model_suitable(
        self,
        model: Dict[str, Any],
        use_case: str
    ) -> bool:
        """Check if Ollama model is suitable for use case."""
        if use_case == "story_generation":
            return model.get("context_length", 0) >= 100000
        if use_case == "npc_dialogue":
            return True  # Most models work for dialogue
        return True
    
    def _calculate_resource_efficiency(self, model: Dict[str, Any]) -> float:
        """Calculate resource efficiency score (0-1)."""
        # Based on size and context length
        size_gb = self._parse_size_to_gb(model.get("size", "10GB"))
        context = model.get("context_length", 0)
        
        # Efficiency = context per GB (higher is better)
        if size_gb > 0:
            efficiency = min(context / (size_gb * 10000), 1.0)
        else:
            efficiency = 0.5  # Default
        
        return efficiency
    
    def _calculate_size_score(self, model: Dict[str, Any]) -> float:
        """Calculate size score (smaller is better, 0-1)."""
        size_gb = self._parse_size_to_gb(model.get("size", "10GB"))
        
        # Score decreases as size increases
        # Ideal: <5GB = 1.0, 5-10GB = 0.8, 10-20GB = 0.5, >20GB = 0.2
        if size_gb < 5:
            return 1.0
        elif size_gb < 10:
            return 0.8
        elif size_gb < 20:
            return 0.5
        else:
            return 0.2
    
    def _calculate_community_score(self, model: Dict[str, Any]) -> float:
        """Calculate community health score (0-1)."""
        downloads = model.get("downloads", 0)
        likes = model.get("likes", 0)
        
        # Normalize based on typical values
        download_score = min(downloads / 1000000, 1.0)  # 1M+ downloads = 1.0
        like_score = min(likes / 10000, 1.0)  # 10K+ likes = 1.0
        
        return (download_score + like_score) / 2
    
    def _calculate_update_score(self, model: Dict[str, Any]) -> float:
        """Calculate recent update score (0-1)."""
        # Default to 0.5 if no update info
        return 0.5
    
    def _parse_size_to_gb(self, size_str: str) -> float:
        """Parse size string to GB."""
        try:
            size_str = size_str.upper().strip()
            if "GB" in size_str:
                return float(size_str.replace("GB", "").strip())
            elif "MB" in size_str:
                return float(size_str.replace("MB", "").strip()) / 1024
            else:
                return 10.0  # Default
        except:
            return 10.0  # Default












