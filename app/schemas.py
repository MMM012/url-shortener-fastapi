from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ---------- Links ----------

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None


class LinkBase(BaseModel):
    short_code: str
    original_url: HttpUrl
    created_at: datetime
    expires_at: Optional[datetime] = None
    click_count: int
    last_accessed_at: Optional[datetime] = None
    custom_alias: Optional[str] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True


class LinkUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    new_short_code: Optional[str] = None


class LinkStats(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    click_count: int
    last_accessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
