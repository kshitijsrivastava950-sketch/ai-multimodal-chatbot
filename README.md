Name: Kshitij Chitransh
Roll Number: 202510101110043
Course: B.Tech CSE (32)

# Multimodal Emotional Support Chatbot (RAG + FastAPI + Streamlit + MySQL + Gemini)

A secure, empathetic multimodal conversational agent designed to provide personal emotional support, grounding exercises, and grounded knowledge retrieval using a RAG architecture.

---

## 🌟 Key Features

1. **Multimodal Input & Output:**
   - **Input:** Accepts Text, Images (`.png`, `.jpg`), Audio (`.wav`, `.mp3`), and Knowledge Base Documents (`.pdf`, `.txt`).
   - **Output:** Empathetic text responses, synthesized voice playback (TTS), and therapeutic imagery.
2. **Strict Guardrails & Crisis Protocol:**
   - Detects acute distress signals (self-harm, suicidal ideation) and immediately triggers free, confidential crisis resources (988 Lifeline, Crisis Text Line, etc.).
   - Defends against prompt injection attacks (`jailbreaks`, `DAN mode`).
   - Anonymizes PII (emails, phone numbers).
   - Clear non-clinical disclaimer.
3. **Multimodal RAG Architecture:**
   - Document chunking and embedding generation via Google Gemini `text-embedding-004`.
   - Vector similarity retrieval dynamically injects coping guides and reference literature into the conversation.
4. **Relational Database Storage:**
   - MySQL for persistent storage of sessions, message history, media links, and document embeddings.
   - Built-in automatic SQLite fallback for rapid local offline testing.

---

## 🏗️ Project Architecture

```text
ai-multimodal-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (chat, rag, sessions)
│   │   ├── core/         # Config, Database engine, Guardrails & Crisis rules
│   │   ├── models/       # SQLAlchemy models (ChatSession, ChatMessage, Document, DocumentChunk)
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── services/     # Gemini Multimodal, TTS audio, and RAG vector engine
│   ├── main.py           # FastAPI entrypoint
│   └── requirements.txt  # Backend dependencies
├── frontend/
│   ├── streamlit_app.py  # Empathetic Streamlit UI with multimodal components
│   └── requirements.txt  # Frontend dependencies
├── media/                # Storage for uploaded files and synthesized audio
├── tests/                # Automated verification tests
├── .env.example          # Environment variables template
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- (Optional) MySQL Server 8.0+

### 2. Environment Setup
Copy the environment template and set your configuration:
```bash
cp .env.example .env
```
Edit `.env` to configure your Gemini API Key and MySQL credentials:
```ini
GEMINI_API_KEY=your_gemini_api_key_here

# MySQL configuration
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=chatbot_db
```
*(If MySQL is not installed or unreachable, the system automatically runs on local SQLite without crashing).*

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 4. Run the Backend API (FastAPI)
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/docs`

### 5. Run the Frontend (Streamlit)
In a separate terminal:
```bash
streamlit run frontend/streamlit_app.py
```
The application will open at: `http://localhost:8501`

---

## 🧪 Running Automated Tests
To test guardrails, RAG vector ingestion, and database operations:
```bash
python tests/test_chatbot.py
```
