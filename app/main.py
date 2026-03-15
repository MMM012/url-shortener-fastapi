from datetime import datetime
import random
import string
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .auth import router as auth_router, get_current_user
from .cache import redis_client, get_link_cache_key

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="URL Shortener",
    version="1.0.0",
    description="Простой сервис укороченных ссылок на FastAPI",
)

app.include_router(auth_router)


def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


@app.post(
    "/links/shorten",
    response_model=schemas.LinkBase,
    status_code=status.HTTP_201_CREATED,
)
def create_short_link(
    link_data: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    short_code = link_data.custom_alias or generate_short_code()

    existing = (
        db.query(models.Link)
        .filter(models.Link.short_code == short_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short code already exists",
        )

    db_link = models.Link(
        short_code=short_code,
        original_url=str(link_data.original_url),
        created_at=datetime.utcnow(),
        expires_at=link_data.expires_at,
        click_count=0,
        last_accessed_at=None,
        custom_alias=link_data.custom_alias,
        owner_id=current_user.id,
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    # Обновим кэш (можно не обязательно, основное — редирект)
    cache_key = get_link_cache_key(short_code)
    redis_client.set(cache_key, db_link.original_url, ex=3600)

    return db_link


@app.get("/{short_code}")
def redirect_short_url(
    short_code: str,
    db: Session = Depends(get_db),
):
    cache_key = get_link_cache_key(short_code)
    cached_url = redis_client.get(cache_key)

    if cached_url:
        return RedirectResponse(
            url=cached_url,
            status_code=status.HTTP_302_FOUND,
        )

    link = (
        db.query(models.Link)
        .filter(models.Link.short_code == short_code)
        .first()
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )

    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link expired",
        )

    link.click_count += 1
    link.last_accessed_at = datetime.utcnow()
    db.add(link)
    db.commit()

    redis_client.set(cache_key, link.original_url, ex=3600)

    return RedirectResponse(
        url=link.original_url,
        status_code=status.HTTP_302_FOUND,
    )


@app.get(
    "/links/{short_code}/stats",
    response_model=schemas.LinkStats,
)
def get_link_stats(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    link = (
        db.query(models.Link)
        .filter(models.Link.short_code == short_code)
        .first()
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )
    if link.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return link


@app.delete(
    "/links/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    link = (
        db.query(models.Link)
        .filter(models.Link.short_code == short_code)
        .first()
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )
    if link.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # чистим кэш
    cache_key = get_link_cache_key(short_code)
    redis_client.delete(cache_key)

    db.delete(link)
    db.commit()
    return


@app.put(
    "/links/{short_code}",
    response_model=schemas.LinkBase,
)
def update_link(
    short_code: str,
    update_data: schemas.LinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    link = (
        db.query(models.Link)
        .filter(models.Link.short_code == short_code)
        .first()
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )
    if link.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if update_data.new_short_code:
        existing = (
            db.query(models.Link)
            .filter(models.Link.short_code == update_data.new_short_code)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short code already exists",
            )
        # чистим старый ключ
        cache_key_old = get_link_cache_key(short_code)
        redis_client.delete(cache_key_old)

        link.short_code = update_data.new_short_code

    if update_data.original_url:
        link.original_url = str(update_data.original_url)

    db.add(link)
    db.commit()
    db.refresh(link)

    # обновим кэш для нового кода
    cache_key_new = get_link_cache_key(link.short_code)
    redis_client.set(cache_key_new, link.original_url, ex=3600)

    return link


@app.get(
    "/links/search",
    response_model=List[schemas.LinkBase],
)
def search_links(
    original_url: str = Query(..., alias="original_url"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    links = (
        db.query(models.Link)
        .filter(
            models.Link.original_url == original_url,
            models.Link.owner_id == current_user.id,
        )
        .all()
    )
    return links
