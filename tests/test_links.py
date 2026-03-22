from datetime import datetime, timedelta

from fastapi import status

from .conftest import client


def test_create_short_link_basic():
    payload = {
        "original_url": "https://example.com",
        "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "custom_alias": None,
    }

    response = client.post("/links/shorten", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "short_code" in data
    assert data["original_url"].rstrip("/") == "https://example.com"


def test_redirect_short_url_not_found():
    response = client.get("/some-not-existing-code", follow_redirects=False)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_link_change_url_and_code():
    create_payload = {
        "original_url": "https://old.com",
        "expires_at": None,
        "custom_alias": "old_update_1001",
    }
    create_resp = client.post("/links/shorten", json=create_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED

    update_payload = {
        "new_short_code": "new_update_1001",
        "original_url": "https://new.com",
    }
    update_resp = client.put("/links/old_update_1001", json=update_payload)
    assert update_resp.status_code == status.HTTP_200_OK
    data = update_resp.json()
    assert data["short_code"] == "new_update_1001"
    assert data["original_url"].rstrip("/") == "https://new.com"

    redirect_resp = client.get("/new_update_1001", follow_redirects=False)
    assert redirect_resp.status_code == status.HTTP_302_FOUND
    assert redirect_resp.headers["location"].rstrip("/") == "https://new.com"


def test_delete_link():
    create_payload = {
        "original_url": "https://delete.me",
        "expires_at": None,
        "custom_alias": "del_delete_1001",
    }
    create_resp = client.post("/links/shorten", json=create_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED

    delete_resp = client.delete("/links/del_delete_1001")
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    stats_resp = client.get("/links/del_delete_1001/stats")
    assert stats_resp.status_code == status.HTTP_404_NOT_FOUND


def test_get_link_stats():
    create_payload = {
        "original_url": "https://stats.com",
        "expires_at": None,
        "custom_alias": "stats_test_1001",
    }
    create_resp = client.post("/links/shorten", json=create_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED

    stats_resp = client.get("/links/stats_test_1001/stats")
    assert stats_resp.status_code == status.HTTP_200_OK
    data = stats_resp.json()

    assert "click_count" in data
    assert "created_at" in data
    assert "last_accessed_at" in data
    assert "original_url" in data
    assert data["click_count"] == 0
    assert data["original_url"].rstrip("/") == "https://stats.com"


def test_search_links():
    create_payload = {
        "original_url": "https://search.me",
        "expires_at": None,
        "custom_alias": None,
    }
    create_resp = client.post("/links/shorten", json=create_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED

    created_data = create_resp.json()
    stored_url = created_data["original_url"]

    search_resp = client.get("/links/search", params={"original_url": stored_url})
    assert search_resp.status_code == status.HTTP_200_OK
    data = search_resp.json()
    assert len(data) >= 1
    assert data[0]["original_url"] == stored_url


def test_create_short_link_duplicate_custom_alias():
    payload = {
        "original_url": "https://dup.com",
        "expires_at": None,
        "custom_alias": "dup_alias_1001",
    }
    resp1 = client.post("/links/shorten", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    resp2 = client.post("/links/shorten", json=payload)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST


def test_update_link_to_existing_short_code_fails():
    payload1 = {
        "original_url": "https://first.com",
        "expires_at": None,
        "custom_alias": "first_code_1001",
    }
    payload2 = {
        "original_url": "https://second.com",
        "expires_at": None,
        "custom_alias": "second_code_1001",
    }
    r1 = client.post("/links/shorten", json=payload1)
    r2 = client.post("/links/shorten", json=payload2)
    assert r1.status_code == status.HTTP_201_CREATED
    assert r2.status_code == status.HTTP_201_CREATED

    update_payload = {
        "new_short_code": "second_code_1001",
        "original_url": "https://first.com/updated",
    }
    update_resp = client.put("/links/first_code_1001", json=update_payload)
    assert update_resp.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_not_existing_link_returns_404():
    resp = client.delete("/links/not_existing_123")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
