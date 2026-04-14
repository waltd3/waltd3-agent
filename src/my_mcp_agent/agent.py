from __future__ import annotations

from openai import OpenAI

from .config import MODEL, OPENAI_API_KEY
from .extractor import extract_memory
from .memory import save_turn, semantic_search_memories
from .models import ChatResult
from .profile import get_profile

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PREFIX = '''
You are a personal AI agent with long-term memory.

Instructions:
- Be practical, concise, and specific.
- Use the supplied profile and retrieved memories when relevant.
- Do not invent personal facts that are not in memory.
- If memory is thin or missing, proceed helpfully anyway.
- Prefer actionable steps and examples.
'''

def _build_context(user_message: str) -> tuple[str, list[dict]]:
    profile = get_profile()
    matched = semantic_search_memories(user_message, limit=5)

    profile_lines = "\n".join(f"- {k}: {v}" for k, v in sorted(profile.items())) or "- none yet"
    memory_lines = "\n".join(
        f"- [{m['type']}] {m['text']} (tags: {m['tags']}, confidence: {m['confidence']})"
        for m in matched
    ) or "- none yet"

    context = f"""{SYSTEM_PREFIX}

Known user profile:
{profile_lines}

Relevant long-term memories:
{memory_lines}
"""
    return context, matched

def chat(user_message: str) -> ChatResult:
    if not _client:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")

    context, matched = _build_context(user_message)
    response = _client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": context},
            {"role": "user", "content": user_message},
        ],
    )
    reply_text = response.output_text.strip()
    save_turn(user_message, reply_text)
    extracted = extract_memory(user_message, reply_text)
    return ChatResult(reply=reply_text, extracted=extracted, matched_memories=matched)
