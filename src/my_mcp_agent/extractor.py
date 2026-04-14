from __future__ import annotations

from openai import OpenAI
from .config import MODEL, OPENAI_API_KEY
from .memory import maybe_upsert_memory
from .models import ExtractedMemory

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

EXTRACTION_PROMPT = '''
You extract durable user memory from a conversation turn.

Save memory only if the information is likely to remain useful in future conversations.
Good memories:
- stable preferences
- dislikes
- recurring workflows
- durable project context
- important environment details
- communication style

Do NOT save:
- one-off requests
- temporary plans
- generic facts
- assistant-generated guesses

Return strict JSON with:
{
  "save": boolean,
  "type": "preference|dislike|workflow|project|environment|style|other",
  "text": "one sentence",
  "tags": ["short", "tags"],
  "confidence": 0.0 to 1.0
}
'''

def extract_memory(user_message: str, assistant_message: str) -> ExtractedMemory | None:
    if not _client:
        return None

    response = _client.responses.parse(
        model=MODEL,
        input=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": f"User message:\n{user_message}\n\nAssistant reply:\n{assistant_message}",
            },
        ],
        text_format=ExtractedMemory,
    )
    extracted = response.output_parsed
    if extracted and extracted.save and extracted.text.strip():
        maybe_upsert_memory(
            text=extracted.text.strip(),
            memory_type=extracted.type,
            tags=extracted.tags,
            confidence=extracted.confidence,
        )
    return extracted
