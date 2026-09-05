import os
from pathlib import Path

from dotenv import load_dotenv
from ollama import chat


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


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
        return "I could not find the answer in the uploaded documents."

    model = os.getenv("OLLAMA_MODEL", "llama3.2")

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

    response = chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.message.content