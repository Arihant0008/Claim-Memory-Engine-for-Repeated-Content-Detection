"""
FastAPI Backend for Mnemonic
Serves the verification API at localhost:8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import create_pipeline

app = FastAPI(title="Mnemonic API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClaimRequest(BaseModel):
    raw_text: str

class VerificationResponse(BaseModel):
    normalized_claim: str | None = None
    cache_hit: bool = False
    verification_result: dict | None = None
    retrieved_evidence: list | None = None
    web_search_results: dict | None = None
    web_search_used: bool = False
    seen_count: int = 0
    timestamp: str

@app.get("/")
def root():
    return {"message": "Mnemonic API", "status": "online"}

@app.post("/verify")
async def verify_claim(request: ClaimRequest):
    """Verify a claim through the multi-agent pipeline."""
    try:
        print(f"\n🔍 Processing claim: {request.raw_text}")
        
        # Create pipeline
        pipeline = create_pipeline()
        
        # Initial state
        initial_state = {
            "raw_text": request.raw_text,
            "image_path": None,
            "normalized_claim": None,
            "claim_embedding": None,
            "retrieved_evidence": None,
            "cache_hit": False,
            "web_search_results": None,
            "web_search_used": False,
            "verification_result": None,
            "memory_update_result": None,
            "timestamp": datetime.now().isoformat(),
            "errors": []
        }
        
        # Run pipeline
        result = pipeline.invoke(initial_state)
        
        print(f"✅ Pipeline result: {result.get('verification_result')}")
        
        # Extract seen count from memory update
        seen_count = 0
        if result.get("memory_update_result"):
            seen_count = result["memory_update_result"].get("seen_count", 0)
        
        # Handle errors in result
        if result.get("errors"):
            print(f"⚠️ Pipeline errors: {result['errors']}")
        
        # Extract verification result and normalize fields
        verification_result = result.get("verification_result", {})
        if verification_result:
            # Map 'explanation' to 'reasoning' for frontend compatibility
            if 'explanation' in verification_result and 'reasoning' not in verification_result:
                verification_result['reasoning'] = verification_result['explanation']
        
        response = {
            "normalized_claim": result.get("normalized_claim"),
            "cache_hit": result.get("cache_hit", False),
            "verification_result": verification_result or {
                "verdict": "ERROR",
                "confidence": 0,
                "reasoning": f"Pipeline errors: {', '.join(result.get('errors', ['Unknown error']))}"
            },
            "retrieved_evidence": result.get("retrieved_evidence"),
            "web_search_results": result.get("web_search_results"),
            "web_search_used": result.get("web_search_used", False),
            "seen_count": seen_count,
            "timestamp": result.get("timestamp", datetime.now().isoformat())
        }
        
        return response
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Error: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Mnemonic API Server...")
    print("📡 Backend: http://localhost:8000")
    print("🔍 Frontend: http://localhost:3000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
