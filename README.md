# URL Shortener (FastAPI)

Сервис сокращения ссылок на FastAPI с авторизацией, статистикой и кэшированием редиректов в Redis.

## API

- POST /auth/register – регистрация.
- POST /auth/login – логин, выдаёт JWT.
- POST /links/shorten – создать короткую ссылку.
- GET /{short_code} – редирект по короткой ссылке.
- GET /links/{short_code}/stats – статистика.
- PUT /links/{short_code} – обновить ссылку.
- DELETE /links/{short_code} – удалить ссылку.
- GET /links/search?original_url=... – поиск по исходному URL.


## Запуск

```bash
python -m venv venv
source venv/bin/activate 
pip install -r requirements.txt

export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="change_me"

redis-server
uvicorn app.main:app --host 0.0.0.0 --port 8000


Документация: http://localhost:8000/docs

База данных
users: id, email, hashed_password, created_at
links: id, short_code, original_url, created_at, expires_at, click_count, last_accessed_at, custom_alias, owner_id


## Тестирование

Функциональные и негативные тесты написаны с использованием pytest и FastAPI TestClient.
Тестируются основные ручки API (создание, обновление, удаление, редирект, статистика и поиск ссылок),
а также сценарии регистрации и авторизации пользователей.

Запуск тестов:

pytest -q

Покрытие и HTML-отчёт:
pytest --cov=app --cov-report=html


Отчёт можно открыть из папки htmlcov/index.html.
Текущее общее покрытие по проекту ~75%


И раздел про нагрузку:

```markdown

## Нагрузочное тестирование

Для нагрузки использовал Locust (`locustfile.py` в корне проекта)

Установка:

pip install locust

Запуск приложения:
uvicorn app.main:app --reload

Запуск Locust:
locust -f locustfile.py --host=http://localhost:8000