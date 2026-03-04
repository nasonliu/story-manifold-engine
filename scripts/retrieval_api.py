#!/usr/bin/env python3
"""
Simple FastAPI server for skeleton retrieval.
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import uvicorn
from retrieval import search, build_index

app = FastAPI(title="Story Skeleton Retrieval API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    # Build index on startup if not exists
    build_index()

@app.get("/search")
def api_search(
    q: str = Query(..., description="Search query"),
    k: int = Query(5, ge=1, le=20, description="Number of results"),
    archetype: Optional[str] = Query(None, description="Filter by archetype"),
    ending: Optional[str] = Query(None, description="Filter by ending type"),
    style: Optional[str] = Query(None, description="Filter by style tags (comma-separated)"),
):
    style_tags = style.split(',') if style else None
    results = search(q, k=k, archetype=archetype, ending=ending, style_tags=style_tags)
    
    return {
        "results": [
            {
                "id": sk.get("id"),
                "title": sk.get("title"),
                "archetype": sk.get("archetype"),
                "ending": sk.get("ending"),
                "logline": sk.get("logline"),
                "style_tags": sk.get("style_tags"),
                "score": round(score, 3),
            }
            for sk, score in results
        ]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
