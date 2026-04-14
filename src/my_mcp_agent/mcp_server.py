from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .agent import chat
from .memory import maybe_upsert_memory, recent_memories, semantic_search_memories
from .profile import get_profile, set_profile

mcp = FastMCP("waltd3-agent")

@mcp.tool()
def chat_tool(message: str) -> dict:
    """Chat with the personal agent. Automatically retrieves relevant memory and extracts durable memory after the reply."""
    result = chat(message)
    return result.model_dump()

@mcp.tool()
def set_profile_value(key: str, value: str) -> dict:
    """Set or update one profile field for the user."""
    set_profile(key, value)
    return {"ok": True, "key": key, "value": value}

@mcp.tool()
def get_profile_tool() -> dict:
    """Return the full saved user profile."""
    return get_profile()

@mcp.tool()
def add_memory_tool(text: str, memory_type: str = "preference", tags_csv: str = "", confidence: float = 0.85) -> dict:
    """Add a long-term memory manually."""
    tags = [tag.strip() for tag in tags_csv.split(",") if tag.strip()]
    return maybe_upsert_memory(text=text, memory_type=memory_type, tags=tags, confidence=confidence)

@mcp.tool()
def search_memories_tool(query: str, limit: int = 5) -> list[dict]:
    """Search memories semantically by meaning using embeddings."""
    return semantic_search_memories(query=query, limit=limit)

@mcp.tool()
def recent_memories_tool(limit: int = 10) -> list[dict]:
    """Return the most recently updated memories."""
    return recent_memories(limit=limit)

if __name__ == "__main__":
    mcp.run(transport="stdio")
