from my_mcp_agent.db import init_db
from my_mcp_agent.profile import set_profile
from my_mcp_agent.memory import maybe_upsert_memory

init_db()

# Example seed values
set_profile("name", "Walter")
set_profile("preferred_tone", "direct, practical")
set_profile("platform", "macOS")
set_profile("preferred_examples", "copy-pasteable commands")

maybe_upsert_memory(
    text="Prefers concise, practical answers with copy-pasteable terminal commands.",
    memory_type="style",
    tags=["style", "mac", "coding"],
    confidence=0.96,
)

maybe_upsert_memory(
    text="Works frequently with Python, Laravel, and MCP-related tooling.",
    memory_type="project",
    tags=["python", "laravel", "mcp"],
    confidence=0.91,
)

print("Database initialized.")
