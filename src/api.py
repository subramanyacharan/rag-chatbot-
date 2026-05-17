from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.phase3_rag_engine.generator import RAGGenerator
import uvicorn
import os

app = FastAPI(title="FundQuest AI API")

# CORS: credentials cannot be used with allow_origins=["*"] (browser blocks the response).
_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Generator
generator = RAGGenerator()

class QueryRequest(BaseModel):
    query: str

@app.get("/")
async def root():
    return {"message": "FundQuest AI API is running", "status": "online"}

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        response_data = generator.generate_structured_response(request.query)
        if response_data.get("status") in ("error", "config_error", "rate_limited"):
            raise HTTPException(status_code=503, detail=response_data.get("answer"))
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get port from environment variable for Railway deployment
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
