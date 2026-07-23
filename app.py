
import os
import json
import pandas as pd
import streamlit as st
from google.colab import userdata

# Import our backend logic engine
from bot_engine import process_matrix_for_llm, build_system_prompt, AriaChatbot

# ---------------------------------------------------------------------------
# 1. INITIALIZATION & DATA SETUP
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Grab Analytics | Aria", page_icon="🚗", layout="wide")

# Get API Key from Secrets or Environment
try:
    gemini_key = userdata.get('GEMINI_API_KEY')
except Exception:
    gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    st.error("🔑 GEMINI_API_KEY not found! Please set it in Secrets or environment variables.")
    st.stop()

# Instantiate Chatbot Engine
bot_engine = AriaChatbot(api_key=gemini_key)

# Load Sample Raw Data
raw_data = {
    'Day': ['Friday', 'Monday'],
    '0': [9.0, 9.0], '1': [10.0, 57.14], '2': [12.0, 46.73], '3': [7.0, 43.4],
    '4': [12.0, 51.4], '6': [10.67, 50.665], '7': [51.65, 84.5825], '8': [5.67, 55.835],
    '9': [3.0, 26.0], '10': [7.0, 9.33], '11': [13.27, 13.27], '12': [87.0, 38.13],
    '13': [27.22, 18.0], '14': [84.67, 24.06], '15': [79.67, 46.2],
    '16': [15.33, 95.2525], '17': [16.67, 98.667], '18': [2.01, 87.443]
}
raw_df = pd.DataFrame(raw_data)

# ---------------------------------------------------------------------------
# 2. STREAMLIT CHAT STATE & SIDEBAR
# ---------------------------------------------------------------------------
st.title("🚗 Grab Analytics: Prescriptive Strategy Partner")
st.caption("Powered by Gemini 3.5 Flash | Prescriptive Engine")

with st.sidebar:
    st.header("📊 Context Data Dashboard")
    st.write("**Descriptive Overview:**")
    st.markdown("""
    - **7 AM - 9 AM Spike:** Avg 13 min EWT
    - **5 PM - 7 PM Spike:** Avg 15 min EWT
    - **Threshold:** >15 mins causes satisfaction drop to < 4.0
    """)
    st.divider()
    st.write("**Predictive Probability Matrix:**")
    st.dataframe(raw_df, use_container_width=True)
    
    if st.button("🗑️ Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

# Initialize System Prompt and Chat Memory
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    processed_summary = process_matrix_for_llm(raw_df)
    system_prompt = build_system_prompt(json.dumps(processed_summary, indent=2))
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# Render Chat History
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = "🚗" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# Trigger initial analysis if starting fresh
if len(st.session_state.messages) == 1:
    initial_user_prompt = "Paki-summarize ang key risk windows natin base sa Random Forest probabilities at bigyan mo ako ng prescriptive options."
    st.session_state.messages.append({"role": "user", "content": initial_user_prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(initial_user_prompt)

    with st.chat_message("assistant", avatar="🚗"):
        with st.spinner("Aria is analyzing predictive probabilities and Grab metrics..."):
            reply = bot_engine.generate_response(st.session_state.messages)
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------------------------------------------------------------------------
# 3. INTERACTIVE CHAT LOOP
# ---------------------------------------------------------------------------
if user_input := st.chat_input("Ask Aria or select a strategic path..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar="🚗"):
        with st.spinner("Aria is formulating strategic options..."):
            try:
                reply = bot_engine.generate_response(st.session_state.messages)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error executing request: {e}")
