from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.db_models import ChatSession, ChatMessage
from backend.app.schemas.chat_schemas import SessionCreate, SessionResponse, MessageResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionResponse)
def create_session(session_in: SessionCreate, db: Session = Depends(get_db)):
    new_session = ChatSession(title=session_in.title)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()

@router.get("/{session_uuid}/messages", response_model=List[MessageResponse])
def get_session_messages(session_uuid: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_uuid == session_uuid).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).all()
