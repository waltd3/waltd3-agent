from __future__ import annotations

import math
from openai import OpenAI
from .config import EMBEDDING_MODEL, OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def has_embedding_client() -> bool:
    return _client is not None

def get_embedding(text: str) -> list[float]:
    if not _client:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")
    response = _client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding

def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
