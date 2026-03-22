from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_current_user


class FakeUser:
    def __init__(self, user_id: int = 1):
        self.id = user_id


def override_get_current_user():
    return FakeUser(user_id=1)


app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)
