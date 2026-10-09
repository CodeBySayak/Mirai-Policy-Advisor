from fastapi.testclient import TestClient
from backend import app
from schemas import ChatRequest

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_chat_empty_question():
    response = client.post("/chat", json={"question": "   "})
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]

def test_ingest_invalid_file_type():
    response = client.post("/ingest", files={"file": ("test.txt", b"Hello", "text/plain")})
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

def test_ingest_empty_pdf():
    response = client.post("/ingest", files={"file": ("test.pdf", b"", "application/pdf")})
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]

# Missing vector store and missing API keys are tested gracefully in backend logic returning 200 with error property.
def test_chat_missing_api_key_or_vector_store():
    # Because API key is not set in test environment, it should return gracefully
    response = client.post("/chat", json={"question": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is not None
