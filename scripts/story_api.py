#!/usr/bin/env python3
"""
Combined Retrieval + Generation API
Core of the A-solution (检索 + LLM 解码)
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# Import our modules
from retrieval import search, build_index
from generate_skeleton import generate_skeleton, generate_with_retrieval, SAMPLING_TEMPLATES

app = FastAPI(title="Story Manifold Engine API")

# Initialize
build_index()

# OpenAI client
from openai import OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

# Request models
class GenerateRequest(BaseModel):
    archetype: str = "复仇"
    ending: str = "tragedy"
    style_tags: Optional[List[str]] = None
    stakes: str = "灵魂"
    template: str = "balanced"  # robust/balanced/exploratory
    use_retrieval: bool = True
    retrieval_k: int = 3
    model: str = "gpt-4o"

class RetrievalRequest(BaseModel):
    query: str
    k: int = 5
    archetype: Optional[str] = None
    ending: Optional[str] = None
    style_tags: Optional[List[str]] = None

@app.get("/health")
def health():
    return {"status": "ok", "phase": "retrieval + generation"}

@app.post("/retrieve")
def retrieve(req: RetrievalRequest):
    """Pure retrieval endpoint."""
    results = search(
        req.query,
        k=req.k,
        archetype=req.archetype,
        ending=req.ending,
        style_tags=req.style_tags,
    )
    
    return {
        "results": [
            {
                "id": sk.get("id"),
                "title": sk.get("title"),
                "archetype": sk.get("archetype"),
                "ending": sk.get("ending"),
                "logline": sk.get("logline"),
                "score": round(score, 3),
            }
            for sk, score in results
        ]
    }

@app.post("/generate")
def generate(req: GenerateRequest):
    """Generate skeleton with optional retrieval augmentation."""
    if not openai_client.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    # Get sampling params
    template = SAMPLING_TEMPLATES.get(req.template, SAMPLING_TEMPLATES["balanced"])
    
    # Retrieval augmentation
    retrieval_results = []
    if req.use_retrieval:
        # Build query from request
        query = f"{req.archetype} {req.ending} {' '.join(req.style_tags or [])} {req.stakes}"
        results = search(query, k=req.retrieval_k, archetype=req.archetype)
        retrieval_results = [sk for sk, _ in results]
    
    # Generate
    if retrieval_results:
        skeleton = generate_with_retrieval(
            openai_client,
            query=f"{req.archetype} {req.ending}",
            retrieval_results=retrieval_results,
            model=req.model,
            temperature=template["temperature"],
        )
    else:
        skeleton = generate_skeleton(
            openai_client,
            archetype=req.archetype,
            ending=req.ending,
            style_tags=req.style_tags,
            stakes=req.stakes,
            model=req.model,
            temperature=template["temperature"],
        )
    
    if not skeleton:
        raise HTTPException(status_code=500, detail="Generation failed")
    
    return {
        "skeleton": skeleton,
        "retrieval_used": bool(retrieval_results),
        "template": req.template,
    }

@app.get("/templates")
def list_templates():
    """List available sampling templates."""
    return {"templates": SAMPLING_TEMPLATES}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8012"))
    uvicorn.run(app, host="0.0.0.0", port=port)
