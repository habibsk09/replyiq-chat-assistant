# ⬡ ReplyIQ — Chat Response Quality & Empathy Assistant

> A Grammarly-style real-time writing coach built specifically for customer-support agents.  
> Fix grammar, inject empathy, improve tone, and score responses — all as you type.

---

## 📸 Overview

ReplyIQ analyses customer-support agent replies in real-time and provides:

| Feature | Detail |
|---|---|
| **Grammar correction** | Capitalization, punctuation, spacing, common typos |
| **Empathy detection** | Flags missing empathy; suggests opening phrases |
| **Tone analysis** | Professional / Neutral / Casual |
| **Smart improvement** | Rewrites the full response like a trained agent |
| **Quality score** | 0–10 breakdown across grammar, empathy, length, tone |
| **Inline highlights** | Underlines errors directly in the textarea |
| **Dark / light mode** | One-click theme toggle |
| **Copy & Apply** | Copy improved text or push it back into the textarea |

---

## 🗂 Project Structure

```
chat-quality-assistant/
├── app.py               # Flask entry point
├── routes.py            # API route definitions
├── quality_checker.py   # Core NLP & scoring logic
├── requirements.txt
├── README.md
├── templates/
│   └── index.html       # Single-page UI
└── static/
    ├── style.css
    └── app.js
```

---

## 🚀 Installation & Running

### 1. Prerequisites
- Python 3.9+
- pip

### 2. Clone / download
```bash
git clone <repo-url>
cd chat-quality-assistant
```

### 3. Create a virtual environment (recommended)
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the server
```bash
python app.py
```

### 6. Open in browser
```
http://localhost:5000
```

---

## 🔌 API Reference

### `POST /check`
Full analysis — call on demand.

**Request**
```json
{ "text": "ok ill check ur order" }
```

**Response**
```json
{
  "original": "ok ill check ur order",
  "corrected": "Okay I'll check your order.",
  "improved": "I understand your concern, and I'm here to help. Okay I'll check your order. Is there anything else I can help you with today?",
  "score": {
    "total": 6.5,
    "label": "Good",
    "breakdown": { "grammar": 3.0, "empathy": 0.0, "length": 1.0, "tone": 0.5 }
  },
  "grammar_errors": [...],
  "empathy": { "has_empathy": false, "suggestion": "I completely understand how frustrating this must be." },
  "tone": "Neutral"
}
```

---

### `POST /realtime`
Lightweight — designed for 500 ms debounced calls while typing.

**Response** (subset of `/check`):
```json
{
  "improved": "...",
  "corrected": "...",
  "score": { "total": 7.0, "label": "Good", "breakdown": {...} },
  "has_empathy": true,
  "empathy_suggestion": "...",
  "tone": "Professional",
  "error_count": 1,
  "grammar_errors": [...]
}
```

---

## 🧠 Scoring Breakdown (10 pts)

| Category | Max | Logic |
|---|---|---|
| Grammar | 4 | −0.5 per error |
| Empathy | 3 | 3 if detected, 0 otherwise |
| Length | 2 | 2 pts ≥15 words, 1 pt ≥8 words |
| Tone | 1 | 1 Professional, 0.5 Neutral, 0 Casual |

---

## 🔮 Future Improvements

- Integrate `language-tool-python` for deep grammatical parsing
- Add sentiment analysis via HuggingFace transformers
- Multi-language support
- Export conversation transcripts as PDF
- Agent leaderboard / analytics dashboard
- Auth system with per-agent history

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| NLP | Rule-based (custom pipeline) |
| Frontend | HTML5, CSS3 (custom variables), Vanilla JS |
| Fonts | Syne (display), DM Sans (body) |

---

## 📄 License
MIT — free to use, modify, and distribute.
