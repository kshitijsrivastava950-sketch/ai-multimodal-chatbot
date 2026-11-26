from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class SessionCreate(BaseModel):
    title: Optional[str] = "Emotional Support Session"

class SessionResponse(BaseModel):
    id: int
    session_uuid: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    role: str
    content_text: str
    input_media_path: Optional[str] = None
    output_media_path: Optional[str] = None
    media_type: Optional[str] = None
    sentiment_flag: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    session_uuid: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    guardrail_triggered: bool = False
    rag_sources: List[str] = []

class DocumentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True
