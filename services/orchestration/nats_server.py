"""
Orchestration Service - NATS Binary Messaging Server
Coordinates complex multi-service workflows

Subjects:
  svc.orchestration.v1.execute_workflow - Execute workflow
  svc.orchestration.v1.get_status - Get workflow status
  svc.orchestration.v1.cancel - Cancel workflow
Events:
  evt.orchestration.workflow.started.v1
  evt.orchestration.workflow.completed.v1
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict
import uuid
import time

sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path))
sys.path.insert(0, str(generated_path))

from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import orchestration_pb2
import common_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestrationNATSService:
    """NATS-based Orchestration service."""
    
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(
            servers=[self.nats_url],
            name="orchestration-service"
        ))
        self.executions: Dict[str, orchestration_pb2.ExecuteWorkflowResponse] = {}
    
    async def handle_execute_workflow(
        self,
        request: orchestration_pb2.ExecuteWorkflowRequest
    ) -> orchestration_pb2.ExecuteWorkflowResponse:
        """Execute a workflow."""
        logger.info(f"Executing workflow {request.workflow_id}: {request.meta.request_id}")
        
        response = orchestration_pb2.ExecuteWorkflowResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            execution_id = f"exec-{uuid.uuid4().hex[:12]}"
            response.execution_id = execution_id
            response.status = "running"
            
            # Store execution
            self.executions[execution_id] = response
            
            logger.info(f"Workflow execution started: {execution_id}")
            return response
        
        except Exception as e:
            logger.error(f"Error executing workflow: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def handle_get_status(
        self,
        request: orchestration_pb2.GetStatusRequest
    ) -> orchestration_pb2.GetStatusResponse:
        """Get workflow status."""
        logger.info(f"Get workflow status {request.execution_id}: {request.meta.request_id}")
        
        response = orchestration_pb2.GetStatusResponse()
        response.meta.CopyFrom(request.meta)
        
        try:
            if request.execution_id not in self.executions:
                response.error.code = common_pb2.Error.NOT_FOUND
                response.error.message = f"Execution not found: {request.execution_id}"
                return response
            
            exec_data = self.executions[request.execution_id]
            response.execution_id = exec_data.execution_id
            response.status = exec_data.status
            response.progress_percentage = 50  # Mock
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting status: {e}", exc_info=True)
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        """Run NATS service workers."""
        logger.info("Starting Orchestration NATS Service")
        logger.info(f"Connecting to NATS at {self.nats_url}")
        
        async with self.client:
            logger.info("Connected to NATS successfully")
            
            tasks = [
                asyncio.create_task(self._execute_worker()),
                asyncio.create_task(self._status_worker()),
            ]
            
            await asyncio.gather(*tasks)
    
    async def _execute_worker(self):
        logger.info("Starting execute workflow worker on svc.orchestration.v1.execute_workflow")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.orchestration.v1.execute_workflow",
            queue="q.orchestration"
        ):
            try:
                request = orchestration_pb2.ExecuteWorkflowRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_execute_workflow(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in execute worker: {e}", exc_info=True)
    
    async def _status_worker(self):
        logger.info("Starting get status worker on svc.orchestration.v1.get_status")
        
        async for msg in self.client.subscribe_queue(
            subject="svc.orchestration.v1.get_status",
            queue="q.orchestration"
        ):
            try:
                request = orchestration_pb2.GetStatusRequest()
                request.ParseFromString(msg.data)
                
                response = await self.handle_get_status(request)
                
                if msg.reply:
                    await msg.respond(response.SerializeToString())
            
            except Exception as e:
                logger.error(f"Error in status worker: {e}", exc_info=True)


async def main():
    service = OrchestrationNATSService()
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

