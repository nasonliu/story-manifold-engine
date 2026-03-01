"""
Story Skeleton Schema & Validator
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional
import json

class Beat(BaseModel):
    id: str
    event: str
    actors: Optional[List[str]] = []
    stakes: Optional[str] = ""

class StorySkeleton(BaseModel):
    id: str
    archetype: List[str]
    beats: List[Beat]
    twist_count: int
    ending: str  # tragedy / triumph / bittersweet / open / pyrrhic
    style_tags: Optional[List[str]] = []

    @field_validator("beats")
    @classmethod
    def check_beats_length(cls, v):
        if not (6 <= len(v) <= 14):
            raise ValueError(f"beats length must be 6–14, got {len(v)}")
        return v

def validate_skeleton(data: dict) -> StorySkeleton:
    return StorySkeleton(**data)

def load_skeletons(path: str) -> List[StorySkeleton]:
    with open(path) as f:
        raw = json.load(f)
    result = []
    for item in raw:
        try:
            result.append(validate_skeleton(item))
        except Exception as e:
            print(f"Skip invalid: {e}")
    return result
