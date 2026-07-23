import os
import json
import pandas as pd
import streamlit as st

# Import backend logic engine
from bot_engine import Aria, process_matrix_for_llm, build_system_prompt

# ---------------------------------------------------------------------------
# 1. INITIALIZATION & DATA SETUP
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Grab Analytics | Aria", page_icon="🚗", layout="wide")

# Fetch GEMINI_API_KEY from Streamlit Secrets or Environment Variables
gemini_key = (
    os.environ.get("GEMINI_API_KEY") 
    or getattr(st, "secrets", {}).get("GEMINI_API_KEY", None)
)

if not gemini_key:
    st.error("🔑 GEMINI_API_KEY not found! Please add it in Streamlit Cloud Settings -> Secrets.")
    st.stop()

# Instantiate Chatbot Engine
try:
    bot_engine = Aria(api_key=gemini_key)
except Exception as e:
    st.error(f"Error initializing Aria engine: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# 2. STREAMLIT CHAT STATE & SIDEBAR
# ---------------------------------------------------------------------------
st.title("🚗 Grab Analytics: Prescriptive Strategy Partner")
st.caption("Powered by Gemini 3.5 Flash | Prescriptive Decision Engine")

with st.sidebar:
    st.header("📊 Context Data Dashboard")
    st.write("**Descriptive Overview:**")
    st.markdown("""
    - **7 AM - 9 AM Spike:** Avg 13 min EWT
    - **5 PM - 7 PM Spike:** Avg 15 min EWT
    - **Threshold:** >15 mins causes satisfaction drop to < 4.0
    """)
    st.divider()
    
    # Load raw CSV preview for the sidebar if available
    try:
        raw_df = pd.read_csv('da_rfc_temps.csv')
        st.write("**Predictive Data Preview:**")
        st.dataframe(raw_df, use_container_width=True)
    except Exception:
        st.info("💡 Predictive matrix CSV (`da_rfc_temps.csv`) active in system context.")
    
    if st.button("🗑️ Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

# Initialize System Prompt and Chat Memory
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    json_data = process_matrix_for_llm('da_rfc_temps.csv')
    system_prompt = build_system_prompt(json_data)
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# Render Chat History
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = "🚗" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# ---------------------------------------------------------------------------
# 3. INTERACTIVE CHAT LOOP
# ---------------------------------------------------------------------------
if user_input := st.chat_input("Say hello to Aria or ask about Grab peak risk windows..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar="🚗"):
        with st.spinner("Aria is thinking..."):
            try:
                reply = bot_engine.generate_response(st.session_state.messages)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error executing request: {e}")
