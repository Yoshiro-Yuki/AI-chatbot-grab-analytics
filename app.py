import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Import backend logic engine
from backend import process_matrix_for_llm, build_system_prompt, Aria

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
    /* Dark aesthetic background polish */
    .main {
        background-color: #0b0f19;
    }
    /* Title Styling */
    .title-text {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        background: linear-gradient(90deg, #00B14F 0%, #00E676 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle-text {
        text-align: center;
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    /* Chat message container styling */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2. SAFE API KEY RETRIEVAL (Render & Local Env friendly)
# ---------------------------------------------------------------------------
def get_api_key(key_name: str) -> str:
    """Retrieve API key safely across Render, local environment, and Google Colab."""
    # 1. Try standard environment variables first (Render / Docker / .env)
    key = os.getenv(key_name)
    if key:
        return key

    # 2. Fallback: Check Google Colab user data if available
    try:
        from google.colab import userdata
        return userdata.get(key_name)
    except (ImportError, Exception):
        pass

    return None

gemini_key = get_api_key('GEMINI_API_KEY')
groq_key = get_api_key('GROQ_API_KEY')

if not gemini_key or not groq_key:
    st.error("🔑 API Key Error: Missing `GEMINI_API_KEY` or `GROQ_API_KEY`. Please configure them under **Environment** settings in Render.")
    st.stop()

# Instantiate Chatbot Engine with both keys
bot_engine = Aria(gemini_key=gemini_key, groq_key=groq_key)

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
# 3. GEOMETRIC BALL ANIMATION COMPONENT (HTML/JS Canvas)
# ---------------------------------------------------------------------------
geometric_ball_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            overflow: hidden;
            background: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        canvas {
            display: block;
            filter: drop-shadow(0 0 15px rgba(0, 230, 118, 0.4));
        }
    </style>
</head>
<body>
    <canvas id="geoCanvas" width="220" height="220"></canvas>
    <script>
        const canvas = document.getElementById('geoCanvas');
        const ctx = canvas.getContext('2d');
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;

        const phi = (1 + Math.sqrt(5)) / 2;
        const radius = 65;

        let vertices = [
            [-1,  phi, 0], [ 1,  phi, 0], [-1, -phi, 0], [ 1, -phi, 0],
            [0, -1,  phi], [0,  1,  phi], [0, -1, -phi], [0,  1, -phi],
            [ phi, 0, -1], [ phi, 0,  1], [-phi, 0, -1], [-phi, 0,  1]
        ].map(v => {
            let len = Math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
            return [v[0]/len * radius, v[1]/len * radius, v[2]/len * radius];
        });

        const edges = [
            [0,1],[0,5],[0,7],[0,10],[0,11],[1,5],[1,7],[1,8],[1,9],[2,3],
            [2,4],[2,6],[2,10],[2,11],[3,4],[3,6],[3,8],[3,9],[4,5],[4,9],
            [4,11],[5,11],[6,7],[6,8],[6,10],[7,10],[8,9],[8,7],[9,5],[10,11]
        ];

        let angleX = 0.005;
        let angleY = 0.008;
        let pulse = 0;

        function project(x, y, z) {
            let scale = 280 / (280 + z);
            return {
                x: cx + x * scale,
                y: cy + y * scale,
                scale: scale
            };
        }

        function rotate() {
            pulse += 0.03;
            let currentPulse = 1 + Math.sin(pulse) * 0.05;

            vertices = vertices.map(([x, y, z]) => {
                let x1 = x * Math.cos(angleY) + z * Math.sin(angleY);
                let z1 = -x * Math.sin(angleY) + z * Math.cos(angleY);
                
                let y2 = y * Math.cos(angleX) - z1 * Math.sin(angleX);
                let z2 = y * Math.sin(angleX) + z1 * Math.cos(angleX);
                
                return [x1, y2, z2];
            });

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            edges.forEach(([i, j]) => {
                let p1 = project(vertices[i][0] * currentPulse, vertices[i][1] * currentPulse, vertices[i][2] * currentPulse);
                let p2 = project(vertices[j][0] * currentPulse, vertices[j][1] * currentPulse, vertices[j][2] * currentPulse);

                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                
                let avgZ = (vertices[i][2] + vertices[j][2]) / 2;
                let alpha = Math.max(0.25, Math.min(1, (avgZ + radius) / (2 * radius)));
                
                ctx.strokeStyle = `rgba(0, 230, 118, ${alpha})`;
                ctx.lineWidth = 1.5 * p1.scale;
                ctx.stroke();
            });

            vertices.forEach(([x, y, z]) => {
                let p = project(x * currentPulse, y * currentPulse, z * currentPulse);
                ctx.beginPath();
                ctx.arc(p.x, p.y, 3 * p.scale, 0, Math.PI * 2);
                ctx.fillStyle = '#00E676';
                ctx.fill();
            });

            requestAnimationFrame(rotate);
        }

        rotate();
    </script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# 4. HEADER & GEOMETRIC BALL LAYOUT
# ---------------------------------------------------------------------------
st.markdown("<h1 class='title-text'>🚗 Grab Analytics: Prescriptive Strategy Partner</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle-text'>Powered by Gemini 3.5 Flash | Prescriptive AI Engine</p>", unsafe_allow_html=True)

# Render Central Geometric Ball Visualizer
col_left, col_center, col_right = st.columns([1, 1, 1])
with col_center:
    components.html(geometric_ball_html, height=210)

# ---------------------------------------------------------------------------
# 5. STREAMLIT SIDEBAR
# ---------------------------------------------------------------------------
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
    
    if st.button("🗑️ Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# 6. CHAT INITIALIZATION & EXECUTION
# ---------------------------------------------------------------------------
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    processed_summary = process_matrix_for_llm()
    system_prompt = build_system_prompt(processed_summary)
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# Render Chat History
for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = "🚗" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# Trigger initial prompt if starting fresh
if len(st.session_state.messages) == 1:
    initial_user_prompt = "Hey there! I'm new here. Can you introduce yourself and tell me what you do?"
    st.session_state.messages.append({"role": "user", "content": initial_user_prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(initial_user_prompt)

    with st.chat_message("assistant", avatar="🚗"):
        with st.spinner("Aria is analyzing predictive probabilities and Grab metrics..."):
            reply = bot_engine.converse(st.session_state.messages)
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

# ---------------------------------------------------------------------------
# 7. INTERACTIVE CHAT LOOP
# ---------------------------------------------------------------------------
if user_input := st.chat_input("Ask Aria or select a strategic path..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant", avatar="🚗"):
        with st.spinner("Aria is formulating strategic options..."):
            try:
                reply = bot_engine.converse(st.session_state.messages)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error executing request: {e}")
