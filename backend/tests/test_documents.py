from io import BytesIO

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def upload_test_document(
    filename: str,
    content: bytes,
):
    return client.post(
        "/documents/upload",
        files={
            "file": (
                filename,
                BytesIO(content),
                "text/plain",
            )
        },
    )


def delete_document(document_id: int):
    return client.delete(
        f"/documents/{document_id}"
    )


def test_list_documents():
    response = client.get(
        "/documents/"
    )

    assert response.status_code == 200
    assert isinstance(
        response.json(),
        list,
    )


def test_upload_document():
    filename = (
        "pytest_policy_unique.txt"
    )

    content = (
        b"Employees receive 20 vacation days "
        b"per calendar year."
    )

    response = upload_test_document(
        filename,
        content,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == filename
    assert data["chunks_created"] > 0
    assert data["embeddings_created"] > 0

    # Clean up test data.
    delete_document(
        data["id"]
    )


def test_duplicate_document_upload():
    filename = (
        "duplicate_policy_unique.txt"
    )

    content = (
        b"Employees receive 20 vacation days "
        b"per calendar year."
    )

    first_response = upload_test_document(
        filename,
        content,
    )

    assert first_response.status_code == 200

    document_id = (
        first_response.json()["id"]
    )

    second_response = upload_test_document(
        filename,
        content,
    )

    assert second_response.status_code == 409

    # Clean up test data.
    delete_document(
        document_id
    )


def test_delete_document():
    filename = (
        "delete_test_unique.txt"
    )

    content = (
        b"This document is used to test "
        b"document deletion."
    )

    upload_response = upload_test_document(
        filename,
        content,
    )

    assert upload_response.status_code == 200

    document_id = (
        upload_response.json()["id"]
    )

    delete_response = delete_document(
        document_id
    )

    assert delete_response.status_code == 200

    delete_data = (
        delete_response.json()
    )

    assert (
        delete_data["document_id"]
        == document_id
    )

    get_response = client.get(
        "/documents/"
    )

    assert get_response.status_code == 200

    remaining_documents = (
        get_response.json()
    )

    remaining_ids = [
        document["id"]
        for document in remaining_documents
    ]

    assert document_id not in remaining_ids