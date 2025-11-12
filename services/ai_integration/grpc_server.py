# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
GE-004: gRPC Server Implementation
Backend gRPC server for AI inference service.
"""

import asyncio
import grpc
from concurrent import futures
from typing import AsyncIterator

import bodybroker_pb2
import bodybroker_pb2_grpc



class AIInferenceServiceServicer(bodybroker_pb2_grpc.AIInferenceServiceServicer):
    """gRPC service implementation for AI inference."""
    
    def __init__(self):
        self.vllm_client = VLLMClient()
        self.multi_tier_router = MultiTierModelRouter(vllm_client=self.vllm_client)
    
    async def RequestDialogue(
        self,
        request: bodybroker_pb2.DialogueRequest,
        context: grpc.aio.ServicerContext
    ) -> bodybroker_pb2.DialogueResponse:
        """Handle unary dialogue request."""
        try:
            # Prepare context for multi-tier router
            context_dict = {
                "npc_id": request.npc_id,
                "tier": request.tier,
                "task_type": "npc_dialogue",
            }
            
            if request.context_json:
                import json
                context_dict.update(json.loads(request.context_json))
            
            # Route request through multi-tier system
            result = await self.multi_tier_router.route_request(
                prompt=request.player_prompt,
                context=context_dict,
                max_tokens=512,
                temperature=0.7
            )
            
            if result.get("success"):
                return bodybroker_pb2.DialogueResponse(
                    dialogue_text=result.get("text", ""),
                    tokens_used=result.get("tokens_used", 0),
                    latency_ms=result.get("latency_ms", 0.0),
                    tier=result.get("tier", ""),
                    model=result.get("model", "")
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(result.get("error", "Generation failed"))
                return bodybroker_pb2.DialogueResponse()
                
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return bodybroker_pb2.DialogueResponse()
    
    async def RequestDialogueStreaming(
        self,
        request: bodybroker_pb2.DialogueRequest,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator[bodybroker_pb2.DialogueToken]:
        """Handle streaming dialogue request."""
        try:
            # Prepare context
            context_dict = {
                "npc_id": request.npc_id,
                "tier": request.tier,
                "task_type": "npc_dialogue",
            }
            
            if request.context_json:
                import json
                context_dict.update(json.loads(request.context_json))
            
            # Use vLLM streaming (if available)
            # For now, simulate streaming by tokenizing response
            result = await self.multi_tier_router.route_request(
                prompt=request.player_prompt,
                context=context_dict,
                max_tokens=512,
                temperature=0.7
            )
            
            if result.get("success"):
                dialogue_text = result.get("text", "")
                tokens = dialogue_text.split()
                
                for i, token in enumerate(tokens):
                    is_complete = (i == len(tokens) - 1)
                    yield bodybroker_pb2.DialogueToken(
                        token=token + (" " if not is_complete else ""),
                        is_complete=is_complete,
                        token_index=i,
                        latency_ms=result.get("latency_ms", 0.0) / len(tokens) if tokens else 0.0
                    )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(result.get("error", "Generation failed"))
                
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
    
    async def HealthCheck(
        self,
        request: bodybroker_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext
    ) -> bodybroker_pb2.HealthCheckResponse:
        """Health check endpoint."""
        try:
            health = await self.vllm_client.health_check()
            healthy = health.get("status") == "healthy"
            
            return bodybroker_pb2.HealthCheckResponse(
                healthy=healthy,
                status="healthy" if healthy else "unhealthy",
                uptime_seconds=0.0  # TODO: Track uptime
            )
        except Exception as e:
            return bodybroker_pb2.HealthCheckResponse(
                healthy=False,
                status=f"error: {str(e)}",
                uptime_seconds=0.0
            )


async def serve():
    """Start gRPC server."""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    bodybroker_pb2_grpc.add_AIInferenceServiceServicer_to_server(
        AIInferenceServiceServicer(), server
    )
    
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    
    await server.start()
    print(f"gRPC server started on {listen_addr}")
    
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())

