from fastapi import APIRouter

from app.models.schemas import AskRequest, AskResponse
from app.services import rag_service

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    return rag_service.answer(payload.question)
