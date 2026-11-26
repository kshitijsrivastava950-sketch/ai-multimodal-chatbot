import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="EmpathyBot | Multimodal Support",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Calming, Warm Aesthetic
st.markdown("""
<style>
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #2D3748;
        font-weight: 600;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #718096;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    .crisis-box {
        background-color: #FFF5F5;
        border-left: 5px solid #E53E3E;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    .source-tag {
        display: inline-block;
        background-color: #EDF2F7;
        color: #4A5568;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "session_uuid" not in st.session_state:
    st.session_state.session_uuid = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: Sessions, Knowledge Base (RAG), and Disclaimers
with st.sidebar:
    st.markdown("### 🌿 Empathy Space")
    st.markdown("*A secure, supportive multimodal companion.*")
    st.divider()

    # Session Management
    if st.button("➕ New Conversation", use_container_width=True):
        try:
            resp = requests.post(f"{BACKEND_URL}/api/sessions/", json={"title": "Emotional Support Session"}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.session_uuid = data["session_uuid"]
                st.session_state.messages = []
                st.rerun()
        except Exception:
            st.session_state.session_uuid = None
            st.session_state.messages = []
            st.rerun()

    if st.session_state.session_uuid:
        st.caption(f"Session ID: `{st.session_state.session_uuid[:8]}...`")

    st.divider()

    # RAG Document Management
    st.markdown("#### 📚 Knowledge Base (RAG)")
    st.caption("Upload coping strategies, self-help guides, or notes (PDF/TXT) to ground the AI's advice.")
    uploaded_doc = st.file_uploader("Upload reference document", type=["pdf", "txt"], key="rag_uploader")
    if uploaded_doc is not None:
        if st.button("Ingest into Knowledge Base", use_container_width=True):
            with st.spinner("Processing document chunks & embeddings..."):
                try:
                    files = {"file": (uploaded_doc.name, uploaded_doc.getvalue(), uploaded_doc.type)}
                    resp = requests.post(f"{BACKEND_URL}/api/rag/upload", files=files, timeout=30)
                    if resp.status_code == 200:
                        doc_info = resp.json()
                        st.success(f"Ingested '{doc_info['file_name']}' ({doc_info['chunk_count']} chunks)!")
                    else:
                        st.error(f"Failed to ingest: {resp.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    # List Ingested Documents
    try:
        doc_resp = requests.get(f"{BACKEND_URL}/api/rag/documents", timeout=3)
        if doc_resp.status_code == 200:
            docs = doc_resp.json()
            if docs:
                st.markdown("**Indexed Documents:**")
                for d in docs:
                    st.caption(f"• {d['file_name']} ({d['chunk_count']} chunks)")
    except Exception:
        pass

    st.divider()
    st.markdown("#### 🛡️ Guardrails & Safety")
    st.info(
        "**Non-Clinical Disclaimer:**\n"
        "This AI companion is designed for personal emotional validation and grounding. "
        "It is **not** a licensed therapist or crisis clinic.\n\n"
        "**Immediate Crisis Helplines:**\n"
        "- **US & Canada:** Call/Text 988\n"
        "- **Crisis Text Line:** Text HOME to 741741\n"
        "- **India:** 9152987821 (iCall)\n"
        "- **International:** [findahelpline.com](https://findahelpline.com/)"
    )

# Main Chat View
st.markdown("<h2 class='main-header'>Empathetic Multimodal Companion</h2>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Share your thoughts through words, voice, or pictures. Take things at your own pace.</p>", unsafe_allow_html=True)

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display user input media if present
        if msg.get("input_media_url"):
            if msg.get("media_type") == "image":
                st.image(msg["input_media_url"], width=300)
            elif msg.get("media_type") == "audio":
                st.audio(msg["input_media_url"])

        # Display assistant output media (Audio / Generated Image)
        if msg.get("audio_url"):
            st.audio(msg["audio_url"], format="audio/mp3")
        if msg.get("image_url"):
            st.image(msg["image_url"], caption="Calming visual generated for you", width=380)

        # Display RAG sources if applicable
        if msg.get("rag_sources"):
            st.markdown(
                "**Sources referenced:** " + " ".join([f"<span class='source-tag'>{s}</span>" for s in msg["rag_sources"]]),
                unsafe_allow_html=True
            )

# Multimodal Input Section
col1, col2 = st.columns([1, 1])
with col1:
    uploaded_image = st.file_uploader("Attach an Image (optional)", type=["png", "jpg", "jpeg"], key="input_img")
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded image preview", width=180)
with col2:
    uploaded_audio = st.file_uploader("Attach Voice / Audio Note (optional)", type=["wav", "mp3"], key="input_aud")
    if uploaded_audio:
        st.audio(uploaded_audio)

opt_col1, opt_col2 = st.columns(2)
with opt_col1:
    enable_speech = st.checkbox("Enable voice response playback (TTS)", value=True)
with opt_col2:
    request_visual = st.checkbox("Generate comforting illustration", value=False)

# Chat text input
user_input = st.chat_input("How are you feeling right now? Share anything on your mind...")

if user_input:
    # Append user message locally for responsive feedback
    user_payload = {
        "role": "user",
        "content": user_input,
        "input_media_url": None,
        "media_type": None
    }
    st.session_state.messages.append(user_payload)

    with st.chat_message("user"):
        st.markdown(user_input)
        if uploaded_image:
            st.image(uploaded_image, width=300)
        if uploaded_audio:
            st.audio(uploaded_audio)

    # Call FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Reflecting with care..."):
            try:
                data = {
                    "message": user_input,
                    "generate_speech_output": "true" if enable_speech else "false",
                    "request_visual": "true" if request_visual else "false"
                }
                if st.session_state.session_uuid:
                    data["session_uuid"] = st.session_state.session_uuid

                files = {}
                if uploaded_image:
                    files["image"] = (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)
                if uploaded_audio:
                    files["audio"] = (uploaded_audio.name, uploaded_audio.getvalue(), uploaded_audio.type)

                response = requests.post(
                    f"{BACKEND_URL}/api/chat/",
                    data=data,
                    files=files if files else None,
                    timeout=60
                )

                if response.status_code == 200:
                    res_json = response.json()
                    st.session_state.session_uuid = res_json["session_uuid"]
                    assistant_text = res_json["assistant_message"]["content_text"]
                    audio_url = res_json.get("audio_url")
                    image_url = res_json.get("image_url")
                    rag_sources = res_json.get("rag_sources", [])
                    guardrail_triggered = res_json.get("guardrail_triggered", False)

                    if guardrail_triggered:
                        st.markdown(f"<div class='crisis-box'>{assistant_text}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(assistant_text)

                    if audio_url:
                        st.audio(audio_url, format="audio/mp3")
                    if image_url:
                        st.image(image_url, caption="Soothing visual", width=380)
                    if rag_sources:
                        st.markdown(
                            "**Sources referenced:** " + " ".join([f"<span class='source-tag'>{s}</span>" for s in rag_sources]),
                            unsafe_allow_html=True
                        )

                    # Save to state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_text,
                        "audio_url": audio_url,
                        "image_url": image_url,
                        "rag_sources": rag_sources,
                        "guardrail_triggered": guardrail_triggered
                    })

                else:
                    st.error(f"Backend returned error: {response.text}")
            except Exception as e:
                st.error(f"Could not reach backend API at {BACKEND_URL}. Ensure the FastAPI server is running. Details: {e}")
