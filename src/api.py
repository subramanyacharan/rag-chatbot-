from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import logging

logging.basicConfig(level=logging.INFO)

_generator = None


def get_generator():
    global _generator
    if _generator is None:
        from src.phase3_rag_engine.generator import RAGGenerator

        logging.info("Initializing RAG pipeline (first request may load models)...")
        _generator = RAGGenerator()
    return _generator


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="FundQuest AI API", lifespan=lifespan)

_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


from typing import Optional

class QueryRequest(BaseModel):
    query: str
    context_fund: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "FundQuest AI API is running", "status": "online"}


@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        response_data = get_generator().generate_structured_response(
            request.query, context_fund=request.context_fund
        )
        if response_data.get("status") in ("error", "config_error", "rate_limited"):
            raise HTTPException(status_code=503, detail=response_data.get("answer"))
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
