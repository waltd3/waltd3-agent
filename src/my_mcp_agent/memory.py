from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Iterable

from .db import get_conn
from .embeddings import cosine_similarity, get_embedding, has_embedding_client

def _normalize_tags(tags: Iterable[str]) -> str:
    clean = sorted({t.strip().lower() for t in tags if t and t.strip()})
    return ",".join(clean)

def add_memory(
    text: str,
    memory_type: str = "preference",
    tags: Iterable[str] = (),
    confidence: float = 0.85,
) -> dict:
    now = datetime.now(UTC).isoformat()
    tag_str = _normalize_tags(tags)
    embedding_json = None
    if has_embedding_client():
        embedding_json = json.dumps(get_embedding(text))
    with get_conn() as conn:
        cur = conn.execute(
            '''
            INSERT INTO memories (type, text, tags, confidence, embedding, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (memory_type, text, tag_str, confidence, embedding_json, now, now),
        )
        conn.commit()
        memory_id = cur.lastrowid
    return get_memory(memory_id)

def get_memory(memory_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, type, text, tags, confidence, embedding, created_at, updated_at FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()
    if not row:
        raise ValueError(f"Memory {memory_id} not found")
    result = dict(row)
    result.pop("embedding", None)
    return result

def recent_memories(limit: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            '''
            SELECT id, type, text, tags, confidence, created_at, updated_at
            FROM memories
            ORDER BY updated_at DESC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]

def keyword_search_memories(query: str, limit: int = 5) -> list[dict]:
    like = f"%{query.lower()}%"
    with get_conn() as conn:
        rows = conn.execute(
            '''
            SELECT id, type, text, tags, confidence, created_at, updated_at
            FROM memories
            WHERE lower(text) LIKE ?
               OR lower(tags) LIKE ?
               OR lower(type) LIKE ?
            ORDER BY confidence DESC, updated_at DESC
            LIMIT ?
            ''',
            (like, like, like, limit),
        ).fetchall()
    return [dict(row) for row in rows]

def semantic_search_memories(query: str, limit: int = 5) -> list[dict]:
    if not has_embedding_client():
        return keyword_search_memories(query, limit=limit)

    query_embedding = get_embedding(query)
    with get_conn() as conn:
        rows = conn.execute(
            '''
            SELECT id, type, text, tags, confidence, embedding, created_at, updated_at
            FROM memories
            WHERE embedding IS NOT NULL
            '''
        ).fetchall()

    scored: list[tuple[float, dict]] = []
    for row in rows:
        data = dict(row)
        raw_embedding = data.pop("embedding", None)
        if not raw_embedding:
            continue
        try:
            emb = json.loads(raw_embedding)
        except json.JSONDecodeError:
            continue
        score = cosine_similarity(query_embedding, emb)
        data["semantic_score"] = round(score, 4)
        scored.append((score, data))

    scored.sort(key=lambda item: (item[0], item[1]["confidence"]), reverse=True)
    results = [item[1] for item in scored[:limit]]

    if results:
        return results

    return keyword_search_memories(query, limit=limit)

def maybe_upsert_memory(
    text: str,
    memory_type: str = "preference",
    tags: Iterable[str] = (),
    confidence: float = 0.85,
) -> dict:
    existing = keyword_search_memories(text[:80], limit=10)
    lowered = text.strip().lower()
    for item in existing:
        if item["text"].strip().lower() == lowered:
            return item
    return add_memory(text=text, memory_type=memory_type, tags=tags, confidence=confidence)

def save_turn(user_message: str, assistant_message: str) -> None:
    now = datetime.now(UTC).isoformat()
    with get_conn() as conn:
        conn.execute(
            '''
            INSERT INTO conversations (user_message, assistant_message, created_at)
            VALUES (?, ?, ?)
            ''',
            (user_message, assistant_message, now),
        )
        conn.commit()

def get_memory_by_id(memory_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            '''
            SELECT id, type, text, tags, confidence, created_at, updated_at
            FROM memories
            WHERE id = ?
            ''',
            (memory_id,),
        ).fetchone()
    return dict(row) if row else None


def update_memory(
    memory_id: int,
    text: str,
    memory_type: str,
    tags: Iterable[str],
    confidence: float,
) -> dict:
    now = datetime.now(UTC).isoformat()
    tag_str = _normalize_tags(tags)

    embedding_json = None
    if has_embedding_client():
        embedding_json = json.dumps(get_embedding(text))

    with get_conn() as conn:
        conn.execute(
            '''
            UPDATE memories
            SET type = ?, text = ?, tags = ?, confidence = ?, embedding = ?, updated_at = ?
            WHERE id = ?
            ''',
            (memory_type, text, tag_str, confidence, embedding_json, now, memory_id),
        )
        conn.commit()

    row = get_memory_by_id(memory_id)
    if not row:
        raise ValueError(f"Memory {memory_id} not found after update")
    return row


def delete_memory(memory_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
