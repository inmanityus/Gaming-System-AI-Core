"""Body Broker Integration Service"""
from fastapi import FastAPI
import uvicorn
from .api_routes import router

app = FastAPI(title="Body Broker Integration Service")
app.include_router(router)


@app.on_event("startup")
async def startup():
    from .complete_workflow import BodyBrokerOrchestrator
    global orchestrator
    orchestrator = BodyBrokerOrchestrator()
    await orchestrator.initialize()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4100)

