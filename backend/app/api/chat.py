import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import UPLOAD_DIR, settings
from backend.app.core.database import get_db
from backend.app.core.guardrails import inspect_guardrails, sanitize_pii
from backend.app.models.db_models import ChatSession, ChatMessage
from backend.app.schemas.chat_schemas import ChatResponse, MessageResponse
from backend.app.services.gemini_service import GeminiService
from backend.app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    session_uuid: Optional[str] = Form(None),
    message: str = Form(...),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    generate_speech_output: bool = Form(True),
    request_visual: bool = Form(False),
    db: Session = Depends(get_db)
):
    # Retrieve or create session
    if session_uuid:
        session = db.query(ChatSession).filter(ChatSession.session_uuid == session_uuid).first()
        if not session:
            session = ChatSession(session_uuid=session_uuid)
            db.add(session)
            db.commit()
            db.refresh(session)
    else:
        session = ChatSession()
        db.add(session)
        db.commit()
        db.refresh(session)

    # Sanitize user PII
    sanitized_prompt = sanitize_pii(message)

    # Save uploaded input media (image or audio) if present
    saved_image_path = None
    saved_audio_path = None
    media_type = None

    if image:
        img_filename = f"img_{uuid.uuid4().hex[:8]}_{image.filename}"
        img_path = UPLOAD_DIR / img_filename
        with open(img_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        saved_image_path = str(img_path)
        media_type = "image"

    if audio:
        audio_filename = f"aud_{uuid.uuid4().hex[:8]}_{audio.filename}"
        aud_path = UPLOAD_DIR / audio_filename
        with open(aud_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        saved_audio_path = str(aud_path)
        media_type = "audio"

    # Save User message to DB
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content_text=sanitized_prompt,
        input_media_path=saved_image_path or saved_audio_path,
        media_type=media_type,
        sentiment_flag="user_input"
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 1. Guardrail Inspection
    is_crisis, is_injection, canned_response = inspect_guardrails(sanitized_prompt)
    rag_sources = []
    output_audio_rel_url = None
    output_image_rel_url = None

    if is_crisis:
        # Immediate crisis bypass response
        assistant_text = canned_response
        sentiment = "crisis_triggered"
        guardrail_triggered = True
    elif is_injection:
        # Prompt injection fallback response
        assistant_text = canned_response
        sentiment = "security_override"
        guardrail_triggered = True
    else:
        guardrail_triggered = False
        sentiment = "supportive"

        # 2. RAG Context Retrieval
        rag_context, rag_sources = RAGService.retrieve_relevant_context(sanitized_prompt)

        # 3. Fetch past conversation history
        history_records = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session.id)\
            .order_by(ChatMessage.created_at.asc())\
            .all()
        chat_history = [{"role": h.role, "content": h.content_text} for h in history_records[-6:]]

        # 4. Gemini Multimodal Generation
        assistant_text = GeminiService.generate_response(
            prompt=sanitized_prompt,
            chat_history=chat_history,
            image_path=saved_image_path,
            audio_path=saved_audio_path,
            rag_context=rag_context
        )

        # 5. Optional image generation if requested
        if request_visual:
            output_image_rel_url = GeminiService.generate_therapeutic_image(sanitized_prompt)

    # 6. Audio / Speech Synthesis Output
    if generate_speech_output:
        output_audio_rel_url = GeminiService.generate_speech(assistant_text)

    # Save Assistant message to DB
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content_text=assistant_text,
        output_media_path=output_audio_rel_url or output_image_rel_url,
        media_type="audio" if output_audio_rel_url else ("image" if output_image_rel_url else "text"),
        sentiment_flag=sentiment
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    audio_full_url = f"{settings.BACKEND_URL}{output_audio_rel_url}" if output_audio_rel_url else None
    image_full_url = f"{settings.BACKEND_URL}{output_image_rel_url}" if output_image_rel_url else None

    return ChatResponse(
        session_uuid=session.session_uuid,
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(assistant_msg),
        audio_url=audio_full_url,
        image_url=image_full_url,
        guardrail_triggered=guardrail_triggered,
        rag_sources=rag_sources
    )
