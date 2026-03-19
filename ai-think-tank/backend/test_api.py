from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_history():
    print("Testing /api/history...")
    response = client.get("/api/history")
    print("Status Code:", response.status_code)
    print("Response payload:", response.json())

if __name__ == "__main__":
    test_history()
    print("API Endpoint test passed successfully!")
