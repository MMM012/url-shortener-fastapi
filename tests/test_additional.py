from datetime import datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.auth import SECRET_KEY, ALGORITHM


client = TestClient(app)


def test_login_non_existing_user_fails():
    form = {
        "username": "no_such_user_1001@example.com",
        "password": "pass1234",
    }
    resp = client.post("/auth/login", data=form)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_with_invalid_token_fails():
    invalid_token = jwt.encode({"sub": "123"}, "WRONG_KEY", algorithm=ALGORITHM)
    headers = {"Authorization": f"Bearer {invalid_token}"}

    resp = client.get("/links/search", headers=headers, params={"original_url": "x"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_redirect_expired_link_returns_404():
    expires_at = (datetime.utcnow() - timedelta(days=1)).isoformat()

    payload = {
        "original_url": "https://expired.com",
        "expires_at": expires_at,
        "custom_alias": "expired_1001",
    }
    create_resp = client.post("/links/shorten", json=payload)
    assert create_resp.status_code == status.HTTP_201_CREATED

    resp = client.get("/expired_1001", follow_redirects=False)
    assert resp.status_code == status.HTTP_404_NOT_FOUND
