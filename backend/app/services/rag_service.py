import os
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from pypdf import PdfReader

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.db_models import Document, DocumentChunk
from backend.app.services.gemini_service import client

logger = logging.getLogger(__name__)

class RAGService:
    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> str:
        """Extracts text content from PDF or TXT files."""
        text = ""
        try:
            if file_type.lower() == "pdf":
                reader = PdfReader(file_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
        return text.strip()

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Splits text into overlapping word chunks."""
        words = text.split()
        if not words:
            return []

        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += (chunk_size - overlap)
        return chunks

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """
        Generates vector embeddings using Gemini text-embedding-004.
        Falls back to a deterministic semantic hash/vector if API key is not present.
        """
        if client:
            try:
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                return response.embedding.values
            except Exception as e:
                logger.error(f"Failed to generate Gemini embedding: {e}")

        # Deterministic lightweight pseudo-embedding for local offline testing
        vec = np.zeros(128, dtype=float)
        for i, word in enumerate(text.lower().split()):
            idx = abs(hash(word)) % 128
            vec[idx] += 1.0 / (i + 1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @classmethod
    def ingest_document(cls, file_name: str, file_path: str, file_type: str) -> Document:
        """
        Reads, chunks, embeds, and saves document into database.
        """
        raw_text = cls.extract_text_from_file(file_path, file_type)
        chunks = cls.chunk_text(raw_text)

        db = SessionLocal()
        try:
            doc = Document(
                file_name=file_name,
                file_path=file_path,
                file_type=file_type,
                chunk_count=len(chunks)
            )
            db.add(doc)
            db.flush()

            for idx, chunk_content in enumerate(chunks):
                emb = cls.get_embedding(chunk_content)
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    chunk_text=chunk_content,
                    embedding_json=json.dumps(emb)
                )
                db.add(db_chunk)

            db.commit()
            db.refresh(doc)
            return doc
        finally:
            db.close()

    @classmethod
    def retrieve_relevant_context(cls, query: str, top_k: int = 3) -> Tuple[str, List[str]]:
        """
        Performs vector cosine similarity search against stored document chunks.
        Returns:
            context_string: Concatenated relevant chunks
            sources: List of file names used as reference
        """
        query_embedding = np.array(cls.get_embedding(query), dtype=float)
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return "", []

        db = SessionLocal()
        try:
            chunks = db.query(DocumentChunk, Document.file_name)\
                       .join(Document, DocumentChunk.document_id == Document.id)\
                       .all()

            if not chunks:
                return "", []

            scored_chunks = []
            for chunk_obj, file_name in chunks:
                try:
                    chunk_vec = np.array(json.loads(chunk_obj.embedding_json), dtype=float)
                    c_norm = np.linalg.norm(chunk_vec)
                    if c_norm > 0:
                        similarity = float(np.dot(query_embedding, chunk_vec) / (query_norm * c_norm))
                        scored_chunks.append((similarity, chunk_obj.chunk_text, file_name))
                except Exception:
                    continue

            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_results = scored_chunks[:top_k]

            relevant_texts = []
            sources = set()
            for score, text, source in top_results:
                if score > 0.15:  # Relevance threshold
                    relevant_texts.append(f"[{source}]: {text}")
                    sources.add(source)

            context_str = "\n\n".join(relevant_texts)
            return context_str, list(sources)
        finally:
            db.close()
