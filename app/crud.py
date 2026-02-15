"""from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import get_password_hash, verify_password

# -------- User CRUD --------

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# -------- Task CRUD --------

def create_task(db: Session, task: schemas.TaskCreate, owner_id: int):
    db_task = models.Task(title=task.title, completed=task.completed, owner_id=owner_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session, owner_id: int):
    return db.query(models.Task).filter(models.Task.owner_id == owner_id).all()

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate, owner_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == owner_id).first()
    if not db_task:
        return None
    if task.title is not None:
        db_task.title = task.title
    if task.completed is not None:
        db_task.completed = task.completed
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int, owner_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == owner_id).first()
    if not db_task:
        return None
    db.delete(db_task)
    db.commit()
    return db_task"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_password_hash


# ── User CRUD ─────────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    hashed_pw = get_password_hash(user_in.password)
    db_user = models.User(email=user_in.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)   # Populate server-generated fields (id, created_at).
    return db_user


# ── Task CRUD ─────────────────────────────────────────────────────────────────

def create_task(
    db: Session,
    task_in: schemas.TaskCreate,
    owner_id: int,
) -> models.Task:
    db_task = models.Task(**task_in.model_dump(), owner_id=owner_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks_by_owner(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
) -> List[models.Task]:
    return (
        db.query(models.Task)
        .filter(models.Task.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_task_by_id(db: Session, task_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def update_task(
    db: Session,
    db_task: models.Task,
    task_update: schemas.TaskUpdate,
) -> models.Task:
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, db_task: models.Task) -> None:
    db.delete(db_task)
    db.commit()