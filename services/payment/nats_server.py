"""Payment Service - NATS Binary Messaging Server
In-game currency and transaction processing

Subjects: svc.payment.v1.process, svc.payment.v1.validate, svc.payment.v1.refund
Events: evt.payment.completed.v1
"""
import asyncio, logging, os, sys, uuid, time, random
from pathlib import Path
from typing import Dict
sdk_path = Path(__file__).parent.parent.parent / "sdk"
generated_path = Path(__file__).parent.parent.parent / "generated"
sys.path.insert(0, str(sdk_path)); sys.path.insert(0, str(generated_path))
from sdk import NATSClient, NATSConfig
from sdk.health_check_http import start_health_check_server
from sdk.health_endpoint import run_health_check_server
import payment_pb2, common_pb2
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentNATSService:
    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.client = NATSClient(NATSConfig(servers=[self.nats_url], name="payment-service"))
        self.balances: Dict[str, Dict[str, int]] = {}  # player_id -> currency_type -> amount
    
    async def handle_process_payment(self, request: payment_pb2.ProcessPaymentRequest) -> payment_pb2.ProcessPaymentResponse:
        response = payment_pb2.ProcessPaymentResponse()
        response.meta.CopyFrom(request.meta)
        try:
            player_id = request.player_id
            currency = request.currency_type
            amount = request.amount
            
            if player_id not in self.balances:
                self.balances[player_id] = {}
            if currency not in self.balances[player_id]:
                self.balances[player_id][currency] = 1000  # Starting balance
            
            if self.balances[player_id][currency] >= amount:
                self.balances[player_id][currency] -= amount
                response.success = True
                response.new_balance = self.balances[player_id][currency]
                response.transaction_id = f"txn-{uuid.uuid4().hex[:12]}"
                response.timestamp_ms = int(time.time() * 1000)
            else:
                response.success = False
                response.error.code = common_pb2.Error.FAILED_PRECONDITION
                response.error.message = "Insufficient balance"
            return response
        except Exception as e:
            response.error.code = common_pb2.Error.INTERNAL
            response.error.message = str(e)
            return response
    
    async def run(self):
        async with self.client:
            logger.info("Payment NATS Service running on svc.payment.v1.process")
            async for msg in self.client.subscribe_queue("svc.payment.v1.process", "q.payment"):
                try:
                    request = payment_pb2.ProcessPaymentRequest()
                    request.ParseFromString(msg.data)
                    response = await self.handle_process_payment(request)
                    if msg.reply: await msg.respond(response.SerializeToString())
                except Exception as e: logger.error(f"Error: {e}")

if __name__ == "__main__": asyncio.run(PaymentNATSService().run())

