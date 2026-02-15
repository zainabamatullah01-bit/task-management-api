from fastapi import FastAPI
from app.models import Base
from app.database import engine
from app.auth import get_current_user

app = FastAPI()

# ✅ This creates all tables defined in models.py
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Task Management API is alive!"}


"""from fastapi import Depends

@app.get("/tasks/me")
def read_my_tasks(current_user: int = Depends(get_current_user)):
    # `current_user` is the user_id extracted from the token
    return {"user_id": current_user, "tasks": "Here you would fetch tasks from DB"}


from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import SessionLocal
from app.auth import create_access_token

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from app.schemas import UserCreate, UserResponse, TaskCreate

@app.post("/users/", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db, user)
    return db_user  # FastAPI now converts it to UserResponse automatically


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}


from app.auth import get_current_user

@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task_route(task: TaskCreate, db: Session = Depends(get_db), user_id: User = Depends(get_current_user)):
    return crud.create_task(db, task, owner_id=user_id)

@app.get("/tasks/", response_model=list[schemas.TaskResponse])
def read_tasks(db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    return crud.get_tasks(db, owner_id=user_id)

@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task_route(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    updated_task = crud.update_task(db, task_id, task, owner_id=user_id)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@app.delete("/tasks/{task_id}")
def delete_task_route(task_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    deleted_task = crud.delete_task(db, task_id, owner_id=user_id)
    if not deleted_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"detail": "Task deleted"}""" 




from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db, Base
from app import models, schemas, crud, auth


Base.metadata.create_all(bind=engine)


# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-ready Task Management REST API with JWT authentication, "
        "built with FastAPI + SQLAlchemy + PostgreSQL."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──────────────────────────────────────────────────────────────────────
# Restrict allow_origins to your actual frontend domains in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    """Simple liveness probe. Returns 200 if the server is running."""
    return {"status": "ok", "version": settings.APP_VERSION}


# ── Auth Endpoints ────────────────────────────────────────────────────────────

@app.post(
    "/login",
    response_model=schemas.Token,
    tags=["Authentication"],
    summary="Login and receive a JWT access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
   
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.email})
    return schemas.Token(access_token=access_token, token_type="bearer")


# ── User Endpoints ────────────────────────────────────────────────────────────

@app.post(
    "/users/",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
    summary="Register a new user",
)
def register_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    
    existing = crud.get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return crud.create_user(db, user_in)


@app.get(
    "/users/me",
    response_model=schemas.UserOut,
    tags=["Users"],
    summary="Get current authenticated user",
)
def read_current_user(
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return the profile of the currently authenticated user."""
    return current_user


# ── Task Endpoints ────────────────────────────────────────────────────────────

@app.post(
    "/tasks/",
    response_model=schemas.TaskOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Create a new task",
)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.create_task(db, task_in, owner_id=current_user.id)


@app.get(
    "/tasks/",
    response_model=list[schemas.TaskOut],
    tags=["Tasks"],
    summary="List all tasks for the current user",
)
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return a paginated list of tasks belonging to the current user.
    Other users' tasks are never included in this response."""
    return crud.get_tasks_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)


@app.get(
    "/tasks/{task_id}",
    response_model=schemas.TaskOut,
    tags=["Tasks"],
    summary="Get a single task by ID",
)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = crud.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return task


@app.put(
    "/tasks/{task_id}",
    response_model=schemas.TaskOut,
    tags=["Tasks"],
    summary="Update a task",
)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = crud.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return crud.update_task(db, task, task_update)


@app.delete(
    "/tasks/{task_id}",
    response_model=schemas.MessageResponse,
    tags=["Tasks"],
    summary="Delete a task",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = crud.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    crud.delete_task(db, task)
    return schemas.MessageResponse(message=f"Task {task_id} deleted successfully")


import uvicorn

if __name__ == "__main__":
    # Run FastAPI with Uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True) 