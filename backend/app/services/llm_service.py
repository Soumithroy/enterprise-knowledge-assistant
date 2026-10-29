import logging
import re

import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

NOT_FOUND = "I could not find the answer in the uploaded documents."


def generate_answer(
    question: str,
    context: str,
    conversation_history: str = "",
) -> str:
    """
    Generate an answer using a local Ollama LLM.

    The model uses retrieved document context as the
    authoritative source of information and can use
    conversation history to understand follow-up questions.
    """

    if not context.strip():
        return NOT_FOUND

    if settings.llm_provider == "extractive":
        return _extractive_answer(question, context)

    history_section = ""

    if conversation_history.strip():
        history_section = f"""
PREVIOUS CONVERSATION:

{conversation_history}
"""

    prompt = f"""
You are an Enterprise Knowledge Assistant.

Answer the user's question using ONLY the document
context provided below.

The previous conversation is provided only to help
understand follow-up questions and references.

Rules:

1. Use the document context as the authoritative source.
2. Do not invent information.
3. Do not use information outside the provided documents.
4. If the answer is not available in the documents, say:
   "I could not find the answer in the uploaded documents."
5. Use previous conversation only for context and continuity.
6. Keep the answer concise and professional.
7. Do not mention embeddings, semantic search, chunks,
   or internal system implementation.

DOCUMENT CONTEXT:

{context}

{history_section}

CURRENT USER QUESTION:

{question}
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        if settings.llm_provider == "openai":
            return _openai_chat(messages)
        return _ollama_chat(messages)
    except Exception as exc:  # LLM down / misconfigured -> degrade gracefully
        logger.warning("LLM provider %s failed (%s); using extractive fallback", settings.llm_provider, exc)
        return _extractive_answer(question, context)


def _ollama_chat(messages: list[dict]) -> str:
    from ollama import Client

    response = Client(host=settings.ollama_host).chat(
        model=settings.ollama_model,
        messages=messages,
    )
    return response.message.content


def _openai_chat(messages: list[dict]) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={"model": settings.openai_model, "messages": messages, "temperature": 0},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


_STOPWORDS = set(
    "the a an is are was what which who how many much do does of to in on for and or "
    "with by at from it this that be can i we you our your".split()
)


def _extractive_answer(question: str, context: str) -> str:
    """No-LLM fallback: return the sentence(s) from the context that best match the question."""
    terms = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if w not in _STOPWORDS}
    content = "\n".join(
        line for line in context.splitlines()
        if line.strip() and not line.startswith(("Source:", "Document ID:", "Chunk:", "Content:", "---"))
    )
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", content) if s.strip()]

    scored = sorted(
        ((len(terms & set(re.findall(r"[a-z0-9]+", s.lower()))), s) for s in sentences),
        key=lambda item: -item[0],
    )
    top_score = scored[0][0] if scored else 0
    best = [s for score, s in scored[:2] if score > 0 and score >= 0.75 * top_score]
    return " ".join(best) if best else NOT_FOUND
