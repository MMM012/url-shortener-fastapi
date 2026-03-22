from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_register_user_success():
    payload = {
        "email": "user1001@example.com",
        "password": "pass1234",
    }

    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == "user1001@example.com"
    assert "id" in data


def test_register_user_duplicate_email_fails():
    payload = {
        "email": "user2001@example.com",
        "password": "pass1234",
    }

    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST


def test_login_success_and_get_token():
    payload = {
        "email": "login_ok_1001@example.com",
        "password": "pass1234",
    }
    reg_resp = client.post("/auth/register", json=payload)
    assert reg_resp.status_code == status.HTTP_201_CREATED

    form = {
        "username": "login_ok_1001@example.com",
        "password": "pass1234",
    }
    resp = client.post("/auth/login", data=form)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_fails():
    payload = {
        "email": "login_fail_1001@example.com",
        "password": "pass1234",
    }
    reg_resp = client.post("/auth/register", json=payload)
    assert reg_resp.status_code == status.HTTP_201_CREATED

    form = {
        "username": "login_fail_1001@example.com",
        "password": "wrongpass",
    }
    resp = client.post("/auth/login", data=form)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
