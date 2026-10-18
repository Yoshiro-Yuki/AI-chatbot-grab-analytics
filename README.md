[README.md](https://github.com/user-attachments/files/33626627/README.md)
# 🚗 Aria: Grab Analytics Prescriptive Strategy Partner

Aria is a Streamlit chatbot that acts as a **Strategy & Prescriptive Analytics Facilitator** for a Grab data scientist. It takes pre-calculated descriptive and predictive analytics on ride-booking wait times and customer satisfaction, then helps stakeholders decide **what to do** about them.

Aria does not recalculate the data. She works as a thought partner who proposes options, weighs trade-offs, recommends a path, and builds an action plan.

---

## Features

- **Prescriptive decision framework**: a 4-step method built into the system prompt:
  1. Strategic options generation (2 to 3 distinct paths)
  2. Trade-off and scenario evaluation (impact, effort, risk)
  3. Decision matrix and recommendation
  4. Action plan and milestones (immediate, short-term, long-term)
- **Taglish support**: replies in English, Tagalog, or Taglish, matching the language the user writes in.
- **Voice and text input**: type in the chat box or record audio, which is transcribed with Google Speech Recognition.
- **Automatic LLM fallback**: uses Gemini first and falls back to Groq (Llama 3.3 70B) on API or rate-limit errors.
- **Conversation memory**: the full message history is sent on every turn, so Aria can follow up on the options she proposed earlier.
- **Custom dark UI**: Grab-green gradient header and a centered welcome screen that disappears after the first message.

---

## Project Structure

```
.
├── app.py              # Streamlit UI, session state, voice input, chat loop
├── backend.py          # Aria class, system prompt, data loader, speech-to-text (used by app.py)
├── bot_engine.py       # Alternate Gemini-only engine with Streamlit secrets support (not used by app.py)
├── requirements.txt    # Python dependencies
└── da_rfc_temps.csv    # Predictive model output (you must provide this)
```

---

## Analytics Context Baked into Aria

The system prompt includes these descriptive findings:

| # | Finding |
|---|---------|
| 1 | Booking spikes at 7AM-9AM (about 13 min wait) and 5PM-7PM (about 15 min wait) |
| 2 | Afternoon and evening windows show high upper-quartile variance |
| 3 | Long-distance trips are **not** the primary cause of long waits |
| 4 | Satisfaction stays high (10 to 7.5) for waits of 0-12 minutes |
| 5 | Satisfaction is at risk (7.5 to 6) for waits of 13-15 minutes |
| 6 | Satisfaction drops sharply (4 to 0) beyond 15 minutes |

The predictive data comes from `da_rfc_temps.csv` and is serialized to JSON for the model.

---

## Getting Started

### 1. Prerequisites

- Python 3.9+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- A [Groq API key](https://console.groq.com/keys)
- An internet connection (Google Speech Recognition is an online service)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies: `streamlit`, `openai`, `pandas`, `groq`, `SpeechRecognition`.

### 3. Add your data

Place `da_rfc_temps.csv` in the same folder as `app.py`.

### 4. Set your API keys

**Linux / macOS**
```bash
export GEMINI_API_KEY="your-gemini-key"
export GROQ_API_KEY="your-groq-key"
```

**Windows (PowerShell)**
```powershell
$env:GEMINI_API_KEY="your-gemini-key"
$env:GROQ_API_KEY="your-groq-key"
```

**Google Colab**: add both keys under *Secrets* (the key icon). `app.py` reads them via `google.colab.userdata`.

**Streamlit Community Cloud**: add both keys under *App settings → Secrets*:
```toml
GEMINI_API_KEY = "your-gemini-key"
GROQ_API_KEY = "your-groq-key"
```

### 5. Run the app

```bash
streamlit run app.py
```

---

## How It Works

```
User (text or voice)
        │
        ▼
   app.py (Streamlit)  ── voice ──►  Google Speech Recognition
        │
        ▼
 Aria.converse(messages)
        │
        ├──► Gemini via OpenAI-compatible endpoint  (primary)
        │         │
        │     APIError / RateLimitError
        │         ▼
        └──► Groq, llama-3.3-70b-versatile  (fallback)
```

1. On first load, `app.py` loads the CSV, builds the system prompt, and stores it as the first message in `st.session_state.messages`.
2. Each user message (typed or transcribed) is appended to the history and sent to `Aria.converse()`.
3. Aria replies, and the reply is appended to the history and rendered.

### Interaction rules built into Aria

- She won't bring up analytics on the first message. She sticks to small talk until the user asks.
- She presents options in small steps instead of dumping everything at once.
- She challenges high-risk or low-impact choices constructively.
- When the user picks an option (e.g. "Option B"), she goes straight to the action plan.

---

## Configuration

| Setting | Location | Default |
|---------|----------|---------|
| Primary model | `backend.py` → `Aria.converse` | `gemini-3.5-flash-lite` |
| Fallback model | `backend.py` → `Aria.converse` | `llama-3.3-70b-versatile` |
| Temperature | `backend.py` → `Aria.converse` | `0.7` |
| Data file | `backend.py` → `process_matrix_for_llm` | `da_rfc_temps.csv` |
| System prompt | `backend.py` → `build_system_prompt` | See file |

---

## Troubleshooting

| Problem | Likely cause / fix |
|---------|--------------------|
| `API Key Error: Missing GEMINI_API_KEY or GROQ_API_KEY` | Both keys must be set. The app stops if either is missing. |
| `FileNotFoundError: da_rfc_temps.csv` | Put the CSV in the working directory, or update the path in `backend.py`. |
| `Could not understand the audio` | Speak clearly and record again, or type your message instead. |
| `Error occured (...)` on voice input | Speech recognition needs internet access. |
| `Model currently experiencing high traffic` | Both Gemini and Groq failed. Wait and retry. |

---

## Known Issues / Notes

- **System prompt data placeholder**: in `backend.py`, `SYSTEM_PROMPT` is a plain string, not an f-string, so `{json_data}` is sent to the model literally instead of being replaced with the CSV contents. `bot_engine.py` uses an f-string and doesn't have this problem. To fix it in `backend.py`, add the `f` prefix (`f"""IDENTITY & ROLE ...`).
- `bot_engine.py` is a standalone Gemini-only variant and is not imported by `app.py`. Use or delete it as needed.
- Conversation history is stored in Streamlit session state, so it resets when the browser session ends.

---

## Tech Stack

- [Streamlit](https://streamlit.io/): UI
- [Google Gemini](https://ai.google.dev/) via the OpenAI-compatible API: primary LLM
- [Groq](https://groq.com/): fallback LLM
- [pandas](https://pandas.pydata.org/): data loading
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/): voice transcription
