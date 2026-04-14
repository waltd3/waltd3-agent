from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field

class ExtractedMemory(BaseModel):
    save: bool = False
    type: str = "preference"
    text: str = ""
    tags: List[str] = Field(default_factory=list)
    confidence: float = 0.8

class ChatResult(BaseModel):
    reply: str
    extracted: ExtractedMemory | None = None
    matched_memories: list[dict] = Field(default_factory=list)
