"""from pydantic import BaseModel, EmailStr
from typing import Optional

# ------------------
# User Schemas
# ------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ------------------
# Task Schemas
# ------------------

class TaskCreate(BaseModel):
    title: str
    completed: Optional[bool] = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    owner_id: int

    model_config = {
        "from_attributes": True  # tells Pydantic to read SQLAlchemy models   
        }


from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=128)  # max 128 chars, truncated internally to 72 bytes


from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True  # allows SQLAlchemy model to be converted"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ── Token Schemas ─────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Minimum 6 characters")


class UserOut(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Task Schemas ──────────────────────────────────────────────────────────────

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    completed: Optional[bool] = None


class TaskOut(TaskBase):
    id: int
    completed: bool
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Generic Response (for delete confirmation)

class MessageResponse(BaseModel):
    message: str