import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import TaskCreate, TaskOut
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = task_service.create_task(
        db, external_id=payload.external_id, input_text=payload.input_text
    )
    return task


@router.post("/mock", response_model=TaskOut)
def create_mock_task(db: Session = Depends(get_db)):
    task = task_service.create_task(
        db,
        external_id=f"mock_{uuid.uuid4().hex[:8]}",
        input_text="Отличный сервис, очень доволен!",
    )
    return task


@router.get("", response_model=list[TaskOut])
def get_tasks(db: Session = Depends(get_db)):
    return task_service.list_tasks(db)
