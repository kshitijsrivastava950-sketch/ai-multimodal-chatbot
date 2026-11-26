import re
from typing import Tuple, Optional

# Crisis intervention triggers (self-harm, suicide, severe violence)
CRISIS_KEYWORDS = [
    r"\bsuicid(e|al)\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bwant to die\b",
    r"\bself[- ]harm\b",
    r"\bhurt myself\b",
    r"\bcut myself\b",
    r"\btake all my pills\b",
    r"\bno reason to live\b",
    r"\bdon'?t want to wake up\b",
    r"\bhang myself\b",
]

CRISIS_REGEX = re.compile("|".join(CRISIS_KEYWORDS), re.IGNORECASE)

# Prompt injection detection patterns
INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"bypass (all )?safety",
    r"you are now (in )?developer mode",
    r"jailbreak",
    r"DAN mode",
    r"system prompt override",
    r"disregard (the )?system prompt",
]

INJECTION_REGEX = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

# PII masking patterns
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

CRISIS_SUPPORT_MESSAGE = (
    "I hear how much pain you are in right now, and I want you to know that you are not alone. "
    "Because your safety and well-being are what truly matter most, please reach out to someone who can help right this second.\n\n"
    "### Immediate Crisis & Support Helplines (Confidential & Free 24/7):\n"
    "- **In the US & Canada:** Call or text **988**, or chat at [988lifeline.org](https://988lifeline.org/)\n"
    "- **Crisis Text Line:** Text **HOME** to **741741**\n"
    "- **In the UK:** Call **111** (NHS) or call Samaritans at **116 123**\n"
    "- **In India:** Call **9152987821** (iCall) or **14416** (Tele-MANAS)\n"
    "- **International:** Find immediate local support at [findahelpline.com](https://findahelpline.com/)\n\n"
    "Please connect with one of these compassionate, trained counselors or a trusted loved one right now. I care about your safety."
)

SYSTEM_PERSONA_PROMPT = """
You are an empathetic, emotionally supportive multimodal AI companion.
Your primary role is to provide a safe, compassionate, judgment-free space for the user to express their feelings, reflect on challenges, and find emotional grounding.

Core Guidelines:
1. Tone & Style: Warm, reflective, gentle, active listener. Validate the user's emotions before offering gentle perspectives.
2. Grounding Exercises: When the user feels anxious, overwhelmed, or stressed, guide them through brief soothing exercises (e.g., box breathing, sensory grounding 5-4-3-2-1).
3. Non-Clinical Boundary: You are an AI companion, NOT a doctor, psychiatrist, or licensed clinical therapist. Never provide medical diagnoses, prescribe treatments, or claim human clinical licensure.
4. Multimodal Awareness:
   - If the user provides an image, acknowledge its emotional context or visual elements empathetically.
   - If audio/voice is used, keep your conversational pace comfortable and supportive.
5. Grounded Knowledge (RAG): If background context or coping literature is provided, naturally weave relevant comforting techniques or insights into your response.
"""

def sanitize_pii(text: str) -> str:
    """Mask email addresses and phone numbers to protect user privacy."""
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    return text

def inspect_guardrails(text: str) -> Tuple[bool, bool, Optional[str]]:
    """
    Evaluates user input against safety guardrails.
    Returns:
        is_crisis (bool): Whether emergency self-harm / suicide trigger was detected.
        is_injection (bool): Whether prompt injection attempts were detected.
        canned_response (Optional[str]): Immediate fallback response if triggered.
    """
    if not text:
        return False, False, None

    if CRISIS_REGEX.search(text):
        return True, False, CRISIS_SUPPORT_MESSAGE

    if INJECTION_REGEX.search(text):
        warning = (
            "I am here to offer a safe and supportive space. Let's focus on how you are feeling "
            "and what I can do to support your well-being today."
        )
        return False, True, warning

    return False, False, None
