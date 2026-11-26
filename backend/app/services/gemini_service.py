import os
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from gtts import gTTS

from backend.app.core.config import settings, AUDIO_OUTPUT_DIR, GENERATED_IMAGE_DIR
from backend.app.core.guardrails import SYSTEM_PERSONA_PROMPT

logger = logging.getLogger(__name__)

# Initialize Google GenAI client if key is available
client = None
if settings.GEMINI_API_KEY:
    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Google GenAI client initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize Google GenAI client: {e}")

class GeminiService:
    @staticmethod
    def generate_response(
        prompt: str,
        chat_history: List[Dict[str, str]] = None,
        image_path: Optional[str] = None,
        audio_path: Optional[str] = None,
        rag_context: Optional[str] = None
    ) -> str:
        """
        Sends multimodal inputs and context to Google Gemini and returns empathetic response.
        """
        if chat_history is None:
            chat_history = []

        # Construct system and context wrapper
        full_prompt_parts = []
        
        system_instruction = SYSTEM_PERSONA_PROMPT
        if rag_context:
            system_instruction += f"\n\n[RELEVANT COPING & SUPPORT CONTEXT FROM KNOWLEDGE BASE]:\n{rag_context}\n"

        if not client:
            # Helpful mock / offline fallback when API key is not yet provided
            logger.warning("GEMINI_API_KEY is not configured. Returning local empathetic fallback.")
            if "breathe" in prompt.lower() or "anxious" in prompt.lower() or "panic" in prompt.lower():
                return (
                    "I hear that you're feeling anxious or overwhelmed. Let's take a slow moment together. "
                    "Try this box breathing technique with me: Breathe in gently for 4 seconds... "
                    "Hold for 4 seconds... Release slowly for 4 seconds... and rest for 4 seconds. "
                    "You are safe in this moment. What is on your mind right now?"
                )
            return (
                f"Thank you for sharing that with me. I hear you, and your feelings are completely valid. "
                f"Whenever you're going through something heavy, taking it one breath at a time makes a difference. "
                f"How can I best support you with this right now?"
            )

        try:
            from google.genai import types
            
            contents = []
            
            # Attach multimodal inputs
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                mime_type = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
                contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

            if audio_path and os.path.exists(audio_path):
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                mime_type = "audio/wav" if audio_path.lower().endswith(".wav") else "audio/mp3"
                contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=mime_type))

            # Append text prompt
            contents.append(prompt)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=800,
                )
            )
            return response.text or "I am listening. Please continue."

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return f"I'm here with you. (Note: Gemini encountered an issue: {str(e)[:150]}. How are you feeling right now?)"

    @staticmethod
    def generate_speech(text: str) -> Optional[str]:
        """
        Converts text response to an audio file using gTTS.
        Returns the relative media path.
        """
        try:
            # Clean text of markdown formatting for clearer speech
            clean_text = text.replace("#", "").replace("*", "").replace("`", "").strip()
            if len(clean_text) > 500:
                clean_text = clean_text[:500] + "..."

            audio_filename = f"response_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = AUDIO_OUTPUT_DIR / audio_filename

            tts = gTTS(text=clean_text, lang='en', slow=False)
            tts.save(str(audio_path))
            return f"/media/audio/{audio_filename}"
        except Exception as e:
            logger.error(f"Error generating speech output: {e}")
            return None

    @staticmethod
    def generate_therapeutic_image(prompt: str) -> Optional[str]:
        """
        Generates a soothing or therapeutic visual (e.g. peaceful landscape, calming pattern).
        """
        if not client:
            return None

        try:
            from google.genai import types
            image_filename = f"generated_{uuid.uuid4().hex[:8]}.png"
            image_path = GENERATED_IMAGE_DIR / image_filename

            # Request calming imagery
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=f"Calming, peaceful, serene digital watercolor illustration: {prompt}",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1"
                )
            )
            
            for generated_image in result.generated_images:
                with open(image_path, "wb") as f:
                    f.write(generated_image.image.image_bytes)
                return f"/media/generated/{image_filename}"
        except Exception as e:
            logger.warning(f"Image generation skipped or unsupported: {e}")
            return None
