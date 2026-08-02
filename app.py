import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from visions.core.agent import VisionsAgent
from visions.core.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visions-api")

app = FastAPI(title="Visions AI - God Mode API")

# Initialize Agent Global
agent = VisionsAgent()

class QueryRequest(BaseModel):
    question: str
    image_base64: Optional[str] = None
    user_id: Optional[str] = "user"
    config: Optional[dict] = None

@app.on_event("startup")
def startup_event():
    try:
        logger.info("🚀 Starting Visions Agent...")
        agent.set_up()
        logger.info("✅ Agent Ready.")
    except Exception as e:
        logger.error(f"❌ Startup Failed: {e}")

@app.get("/health")
def health_check():
    return {"status": "online", "agent": "Visions v3.0"}

@app.post("/query")
async def handle_query(request: QueryRequest):
    try:
        logger.info(f"📨 Received query from {request.user_id}")
        response = agent.query(
            question=request.question,
            image_base64=request.image_base64,
            user_id=request.user_id,
            config=request.config
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"❌ Query Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
