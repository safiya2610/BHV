import os
import pytest
from fastapi.testclient import TestClient


os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["GOOGLE_CLIENT_ID"] = "test_client_id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test_client_secret"
os.environ["GOOGLE_REDIRECT_URI"] = "test_redirect_uri"

from main import app


@pytest.fixture
def client():
    return TestClient(app)
