import os
import json
import pandas as pd
import streamlit as st

# Import backend logic engine
from backend import process_matrix_for_llm, build_system_prompt, Aria
from backend import transcribe_voice_from_file as speech_to_text

# ---------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM STYLING
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Grab Analytics | Aria", 
    page_icon="🚗", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI Enhancement
st.markdown("""
<style>
    .main {
        background-color: #0b0f19;
    }

    .header {
        text-align: center;
        padding-top: 15px;
        padding-bottom: 10px;
    }

    .header-title {
        font-size: 36px;
        font-weight: 700;
        background: linear-gradient(90deg, #00B14F, #00E676);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .header-subtitle {
        color: #94A3B8;
        font-size: 14px;
        margin-top: 4px;
    }

    .centered-welcome {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-top: 12vh;
        margin-bottom: 25px;
    }

    .centered-welcome h1 {
        font-family: system-ui, -apple-system, sans-serif; 
        font-size: 32px;
        font-weight: 300;
        color: #e2e8f0;       
        letter-spacing: -0.5px;
        margin-bottom: 8px;
    }

    .centered-welcome p {
        color: #64748b;
        font-size: 15px;
    }

    .stChatMessage {
        border-radius: 18px;
        margin-bottom: 12px;
    }

    /* Container for bottom controls */
    .input-control-box {
        background-color: #161b26;
        padding: 12px;
        border-radius: 16px;
        margin-bottom: 10px;
        border: 1px solid #232a3b;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. SAFE API KEY RETRIEVAL
# ---------------------------------------------------------------------------

def get_api_key(key_name: str) -> str:
    key = os.getenv(key_name)
    if key:
        return key
    try:
        from google.colab import userdata
        return userdata.get(key_name)
    except (ImportError, Exception):
        pass
    return None

gemini_key = get_api_key('GEMINI_API_KEY')
groq_key = get_api_key('GROQ_API_KEY')

if not gemini_key or not groq_key:
    st.error("🔑 API Key Error: Missing `GEMINI_API_KEY` or `GROQ_API_KEY`.")
    st.stop()

# Instantiate Chatbot Engine
bot_engine = Aria(gemini_key=gemini_key, groq_key=groq_key)

# ---------------------------------------------------------------------------
# 3. SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    processed_summary = process_matrix_for_llm()
    system_prompt = build_system_prompt(processed_summary)
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# ---------------------------------------------------------------------------
# 4. HEADER
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="header">
        <div class="header-title">Grab Analytics: Prescriptive Strategy Partner</div>
        <div class="header-subtitle">Powered by Gemini Flash | Prescriptive AI Engine</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# 5. INITIAL WELCOME MESSAGE (Disappears after 1st user query)
# ---------------------------------------------------------------------------
is_initial_state = len(st.session_state.messages) == 1

if is_initial_state:
    st.markdown(
        """
        <div class="centered-welcome">
            <h1>Let’s explore your data. What are you looking for?</h1>
            <p>Speak or type to ask Aria about trends, driver metrics, or prescriptive actions.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------------
# 6. RENDER CHAT HISTORY
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = "🚗" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# ---------------------------------------------------------------------------
# 7. CHAT INPUT WITH AUDIO + TEXT
# ---------------------------------------------------------------------------
# Persistent audio state
if "pending_voice" not in st.session_state:
    st.session_state.pending_voice = ""

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

audio_value = st.audio_input(
    "🎤 Voice input")

if audio_value is not None:
    if audio_value != st.session_state.last_audio:
        st.session_state.last_audio = audio_value
        with st.spinner("Transcribing..."):
            try:
                st.session_state.pending_voice = speech_to_text(audio_value)
            except Exception as err:
                st.error(f"Voice error: {err}")

# Text chat input stays at bottom automatically
user_prompt = st.chat_input(
    "Ask Aria..."
)

# If voice transcription exists, use it
if not user_prompt and st.session_state.pending_voice:
    user_prompt = st.session_state.pending_voice
    st.session_state.pending_voice = ""


# ---------------------------------------------------------------------------
# 8. PROCESS USER INPUT
# ---------------------------------------------------------------------------

if user_prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_prompt
        }
    )

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)


    with st.chat_message("assistant", avatar="🚗"):
        with st.spinner("Aria is formulating strategic options..."):
            try:
                reply = bot_engine.converse(
                    st.session_state.messages
                )

                st.markdown(reply)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": reply
                    }
                )

            except Exception as e:
                st.error(
                    f"Error executing request: {e}"
                )