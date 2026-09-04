import os
from pathlib import Path

from dotenv import load_dotenv
from ollama import chat


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[2]

ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_FILE
)


# ============================================================
# GENERATE AI ANSWER
# ============================================================

def generate_answer(
    question: str,
    context: str,
) -> str:
    """
    Generate a grounded answer using the local Ollama model.
    """

    if not context.strip():
        return (
            "I could not find relevant information "
            "in the uploaded documents."
        )

    model = os.getenv(
        "OLLAMA_MODEL",
        "llama3.2",
    )

    prompt = f"""
You are an Enterprise Knowledge Assistant.

Answer the user's question using ONLY the document
context provided below.

Rules:

1. Do not invent information.
2. Do not use information outside the provided context.
3. If the answer is not available in the context, say:
   "I could not find the answer in the uploaded documents."
4. Keep the answer concise and professional.
5. Do not mention embeddings, semantic search, chunks,
   or internal system implementation.

DOCUMENT CONTEXT:

{context}

USER QUESTION:

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