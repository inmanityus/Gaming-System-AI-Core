"""
SRL Model Adapter - Loads and serves SRL-trained models and LoRA adapters
Integrates with vLLM/TensorRT-LLM for production serving
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for model_management imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))



class SRLModelAdapter:
    """
    Adapter for loading and serving SRL-trained models and LoRA adapters.
    Integrates with vLLM/TensorRT-LLM for production serving.
    """
    
    def __init__(self, model_registry: Optional[ModelRegistry] = None):
        """
        Initialize SRL Model Adapter.
        
        Args:
            model_registry: Model registry instance for model registration
        """
        self.model_registry = model_registry or ModelRegistry()
        self.s3_client = boto3.client('s3')
        self._loaded_models: Dict[str, Any] = {}
        self._loaded_loras: Dict[str, Dict[str, Any]] = {}
        
    async def load_srl_model(
        self,
        model_s3_uri: str,
        model_name: str,
        tier: str,
        use_vllm: bool = True,
        quantization: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load an SRL-trained model from SageMaker output.
        
        Args:
            model_s3_uri: S3 URI to model artifacts
            model_name: Name of the model
            tier: Model tier (gold, silver, bronze)
            use_vllm: Whether to use vLLM (True) or TensorRT-LLM (False)
            quantization: Quantization method (awq, gptq, None for none)
        
        Returns:
            Model configuration dictionary
        """
        try:
            # Parse S3 URI
            bucket, key = self._parse_s3_uri(model_s3_uri)
            
            # Download model artifacts to local cache
            local_path = await self._download_model_artifacts(bucket, key, model_name)
            
            # Load model using vLLM or TensorRT-LLM
            if use_vllm:
                model = await self._load_vllm_model(local_path, model_name, quantization)
            else:
                model = await self._load_tensorrt_model(local_path, model_name, quantization)
            
            # Register model in registry
            model_id = await self.model_registry.register_model(
                model_name=f"{model_name}-srl-{tier}",
                model_type="self_hosted",
                provider="sagemaker",
                use_case=f"srl_{tier}_tier",
                version="1.0",
                model_path=local_path,
                configuration={
                    "tier": tier,
                    "training_method": "srl_rlvr",
                    "serving_backend": "vllm" if use_vllm else "tensorrt",
                    "quantization": quantization,
                    "s3_uri": model_s3_uri
                },
                resource_requirements={
                    "gpu_memory_gb": self._estimate_gpu_memory(tier),
                    "vram_required": True
                }
            )
            
            # Cache loaded model
            self._loaded_models[model_name] = {
                "model": model,
                "model_id": model_id,
                "tier": tier,
                "local_path": local_path
            }
            
            return {
                "model_id": str(model_id),
                "model_name": model_name,
                "tier": tier,
                "status": "loaded",
                "local_path": local_path
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to load SRL model {model_name}: {e}")
    
    async def load_lora_adapter(
        self,
        lora_s3_uri: str,
        adapter_name: str,
        base_model_name: str,
        tier: str
    ) -> Dict[str, Any]:
        """
        Load a LoRA adapter trained via SRL→RLVR pipeline.
        
        Args:
            lora_s3_uri: S3 URI to LoRA adapter files
            adapter_name: Name of the adapter (e.g., "vampire_lora")
            base_model_name: Name of the base model to attach adapter to
            tier: Model tier
        
        Returns:
            Adapter configuration dictionary
        """
        try:
            # Check if base model is loaded
            if base_model_name not in self._loaded_models:
                raise ValueError(f"Base model {base_model_name} not loaded")
            
            base_model = self._loaded_models[base_model_name]["model"]
            
            # Parse S3 URI
            bucket, key = self._parse_s3_uri(lora_s3_uri)
            
            # Download LoRA adapter files
            local_path = await self._download_lora_adapter(bucket, key, adapter_name)
            
            # Load adapter into vLLM model
            if hasattr(base_model, 'load_lora'):
                base_model.load_lora(adapter_name, local_path)
            else:
                # Fallback: manual LoRA loading
                await self._load_lora_manual(base_model, local_path, adapter_name)
            
            # Cache adapter
            self._loaded_loras[adapter_name] = {
                "adapter_name": adapter_name,
                "base_model": base_model_name,
                "tier": tier,
                "local_path": local_path,
                "s3_uri": lora_s3_uri
            }
            
            return {
                "adapter_name": adapter_name,
                "base_model": base_model_name,
                "status": "loaded",
                "local_path": local_path
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to load LoRA adapter {adapter_name}: {e}")
    
    async def unload_lora_adapter(self, adapter_name: str) -> bool:
        """
        Unload a LoRA adapter to free memory.
        
        Args:
            adapter_name: Name of the adapter to unload
        
        Returns:
            True if successful
        """
        if adapter_name not in self._loaded_loras:
            return False
        
        adapter_info = self._loaded_loras[adapter_name]
        base_model = self._loaded_models[adapter_info["base_model"]]["model"]
        
        # Unload adapter from model
        if hasattr(base_model, 'unload_lora'):
            base_model.unload_lora(adapter_name)
        else:
            await self._unload_lora_manual(base_model, adapter_name)
        
        # Remove from cache
        del self._loaded_loras[adapter_name]
        
        return True
    
    async def generate_with_adapter(
        self,
        base_model_name: str,
        adapter_name: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using base model with LoRA adapter.
        
        Args:
            base_model_name: Name of the base model
            adapter_name: Name of the LoRA adapter
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        if base_model_name not in self._loaded_models:
            raise ValueError(f"Base model {base_model_name} not loaded")
        
        if adapter_name not in self._loaded_loras:
            raise ValueError(f"Adapter {adapter_name} not loaded")
        
        base_model = self._loaded_models[base_model_name]["model"]
        
        # Generate with adapter
        if hasattr(base_model, 'generate'):
            # vLLM-style generation
            from vllm import SamplingParams
            
            sampling_params = SamplingParams(
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            outputs = base_model.generate(
                [prompt],
                sampling_params,
                lora_request=adapter_name if hasattr(base_model, 'generate') else None
            )
            
            return outputs[0].outputs[0].text
        else:
            # Fallback generation
            return await self._generate_fallback(base_model, prompt, max_tokens, temperature)
    
    def _parse_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """Parse S3 URI into bucket and key."""
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        
        uri = s3_uri[5:]  # Remove "s3://"
        parts = uri.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        return bucket, key
    
    async def _download_model_artifacts(
        self,
        bucket: str,
        key: str,
        model_name: str
    ) -> str:
        """Download model artifacts from S3 to local cache."""
        cache_dir = Path(".cache/srl_models")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = cache_dir / model_name
        
        # Download all files in the S3 prefix
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=key)
        
        local_path.mkdir(parents=True, exist_ok=True)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                object_key = obj['Key']
                local_file = local_path / object_key.replace(key, "").lstrip("/")
                
                # Create parent directories
                local_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file
                self.s3_client.download_file(bucket, object_key, str(local_file))
        
        return str(local_path)
    
    async def _download_lora_adapter(
        self,
        bucket: str,
        key: str,
        adapter_name: str
    ) -> str:
        """Download LoRA adapter files from S3."""
        cache_dir = Path(".cache/srl_loras")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = cache_dir / adapter_name
        
        # Download adapter files
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=key)
        
        local_path.mkdir(parents=True, exist_ok=True)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                object_key = obj['Key']
                local_file = local_path / object_key.replace(key, "").lstrip("/")
                local_file.parent.mkdir(parents=True, exist_ok=True)
                self.s3_client.download_file(bucket, object_key, str(local_file))
        
        return str(local_path)
    
    async def _load_vllm_model(
        self,
        model_path: str,
        model_name: str,
        quantization: Optional[str]
    ) -> Any:
        """Load model using vLLM."""
        try:
            from vllm import LLM
            
            llm_config = {
                "model": model_path,
                "enable_lora": True,
                "max_lora_rank": 64,
                "max_loras": 20
            }
            
            if quantization:
                llm_config["quantization"] = quantization
            
            return LLM(**llm_config)
            
        except ImportError:
            raise RuntimeError("vLLM not installed. Install with: pip install vllm")
    
    async def _load_tensorrt_model(
        self,
        model_path: str,
        model_name: str,
        quantization: Optional[str]
    ) -> Any:
        """Load model using TensorRT-LLM."""
        try:
            from tensorrt_llm import LLM
            
            llm_config = {
                "model_path": model_path,
                "enable_lora": True
            }
            
            if quantization:
                llm_config["quantization"] = quantization
            
            return LLM(**llm_config)
            
        except ImportError:
            raise RuntimeError("TensorRT-LLM not installed")
    
    async def _load_lora_manual(
        self,
        model: Any,
        lora_path: str,
        adapter_name: str
    ):
        """
        Manual LoRA loading (fallback when vLLM/TensorRT LoRA support unavailable).
        
        This loads LoRA weights and applies them to the model manually.
        """
        import os
        from pathlib import Path
        
        try:
            # Try to use PEFT library for LoRA loading
            try:
                from peft import PeftModel, PeftConfig
                
                # Load LoRA config
                config = PeftConfig.from_pretrained(lora_path)
                
                # Load LoRA weights
                if hasattr(model, 'load_adapter'):
                    # If model supports adapters directly
                    model.load_adapter(lora_path, adapter_name=adapter_name)
                else:
                    # Use PEFT to load adapter
                    peft_model = PeftModel.from_pretrained(model, lora_path, adapter_name=adapter_name)
                    # Merge adapter weights into base model
                    peft_model = peft_model.merge_and_unload()
                    # Update model reference (this depends on backend)
                    if hasattr(model, 'set_peft_model'):
                        model.set_peft_model(peft_model)
                    else:
                        logger.warning(f"Model {type(model)} doesn't support PEFT model setting")
                
                logger.info(f"Loaded LoRA adapter {adapter_name} using PEFT")
                
            except ImportError:
                # PEFT not available, try manual loading
                logger.warning("PEFT not available, attempting manual LoRA loading")
                
                # Check for LoRA weight files
                lora_path_obj = Path(lora_path)
                
                # Look for adapter_model.bin or adapter_model.safetensors
                adapter_files = [
                    lora_path_obj / "adapter_model.bin",
                    lora_path_obj / "adapter_model.safetensors",
                    lora_path_obj / "pytorch_model.bin"
                ]
                
                adapter_file = None
                for file_path in adapter_files:
                    if file_path.exists():
                        adapter_file = file_path
                        break
                
                if adapter_file:
                    # Load weights manually
                    import torch
                    if adapter_file.suffix == ".safetensors":
                        try:
                            from safetensors import safe_open
                            with safe_open(adapter_file, framework="pt") as f:
                                lora_weights = {}
                                for key in f.keys():
                                    lora_weights[key] = f.get_tensor(key)
                        except ImportError:
                            logger.warning("safetensors not available, cannot load LoRA weights")
                            raise RuntimeError("safetensors required for LoRA loading")
                    else:
                        lora_weights = torch.load(adapter_file, map_location="cpu")
                    
                    # Apply LoRA weights to model
                    # This is backend-specific and may need adjustment
                    if hasattr(model, 'load_state_dict'):
                        # Try to load state dict with strict=False
                        model.load_state_dict(lora_weights, strict=False)
                    else:
                        logger.warning(f"Model {type(model)} doesn't support load_state_dict")
                    
                    logger.info(f"Loaded LoRA adapter {adapter_name} manually")
                else:
                    raise FileNotFoundError(f"No LoRA adapter files found in {lora_path}")
                    
        except Exception as e:
            logger.error(f"Error loading LoRA adapter manually: {e}")
            raise RuntimeError(f"Failed to load LoRA adapter {adapter_name}: {e}")
    
    async def _unload_lora_manual(
        self,
        model: Any,
        adapter_name: str
    ):
        """Manual LoRA unloading (fallback)."""
        # Implementation depends on model backend
        pass
    
    async def generate_with_base_model(
        self,
        base_model_name: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using base model without LoRA adapter.
        
        Args:
            base_model_name: Name of the base model
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        if base_model_name not in self._loaded_models:
            raise ValueError(f"Base model {base_model_name} not loaded")
        
        base_model = self._loaded_models[base_model_name]["model"]
        
        # Generate with base model
        if hasattr(base_model, 'generate'):
            # vLLM-style generation
            from vllm import SamplingParams
            
            sampling_params = SamplingParams(
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            outputs = base_model.generate(
                [prompt],
                sampling_params
            )
            
            return outputs[0].outputs[0].text
        else:
            # Fallback generation
            return await self._generate_fallback(base_model, prompt, max_tokens, temperature)
    
    async def _generate_fallback(
        self,
        model: Any,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Fallback generation method."""
        # Implementation depends on model backend
        return ""
    
    def _estimate_gpu_memory(self, tier: str) -> int:
        """Estimate GPU memory requirements based on tier."""
        memory_estimates = {
            "gold": 4,      # 3B-8B models
            "silver": 8,    # 7B-13B models
            "bronze": 32   # 671B MoE (distributed)
        }
        return memory_estimates.get(tier, 8)
    
    async def close(self):
        """Clean up resources."""
        # Unload all adapters
        for adapter_name in list(self._loaded_loras.keys()):
            await self.unload_lora_adapter(adapter_name)
        
        # Models will be cleaned up by garbage collection
        self._loaded_models.clear()
        self._loaded_loras.clear()

