from io import BytesIO

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

POLICY = (
    b"Company Remote Work Policy. Employees may work remotely up to three days per week. "
    b"Remote work requests should be submitted through the employee portal. "
    b"Managers are responsible for approving remote work schedules."
)


def _upload(name: str = "remote_policy_chat_test.txt"):
    response = client.post(
        "/documents/upload",
        files={"file": (name, BytesIO(POLICY), "text/plain")},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_ask_returns_grounded_answer_with_sources():
    document_id = _upload()
    try:
        response = client.post(
            "/chat/ask",
            json={"question": "How many days per week can employees work remotely?"},
        )
        assert response.status_code == 200
        body = response.json()

        assert "three days per week" in body["answer"]
        assert body["sources"][0]["filename"] == "remote_policy_chat_test.txt"
        assert body["conversation_id"] > 0
    finally:
        client.delete(f"/documents/{document_id}")


def test_conversation_history_is_persisted():
    document_id = _upload("history_policy_test.txt")
    try:
        first = client.post("/chat/ask", json={"question": "Who approves remote work schedules?"}).json()
        conversation_id = first["conversation_id"]

        client.post(
            "/chat/ask",
            json={"question": "Where are requests submitted?", "conversation_id": conversation_id},
        )

        conversation = client.get(f"/chat/conversations/{conversation_id}").json()
        roles = [message["role"] for message in conversation["messages"]]
        assert roles == ["user", "assistant", "user", "assistant"]
    finally:
        client.delete(f"/documents/{document_id}")


def test_empty_question_rejected():
    assert client.post("/chat/ask", json={"question": "   "}).status_code == 400


def test_unknown_conversation_returns_404():
    assert client.get("/chat/conversations/999999").status_code == 404


def test_unsupported_file_type_rejected():
    response = client.post(
        "/documents/upload",
        files={"file": ("malware.exe", BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert response.status_code == 400
