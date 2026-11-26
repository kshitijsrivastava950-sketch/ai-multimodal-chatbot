import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings, MEDIA_DIR
from backend.app.core.database import Base, engine
from backend.app.api import sessions, chat, rag

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create tables in Database on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multimodal Emotional Support Chatbot API",
    description="Secure, empathetic multimodal chatbot powered by Google Gemini, RAG, and FastAPI.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media directory for serving generated audio, uploaded images, etc.
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

# Include Routers
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(rag.router, prefix="/api")

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "Multimodal Emotional Support Chatbot API",
        "guardrails_active": settings.ENABLE_STRICT_GUARDRAILS,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
