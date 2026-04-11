"""
quality_checker.py — Core NLP module
Handles grammar correction, empathy detection, tone analysis,
response improvement, and quality scoring.
"""

import re
import math
import random
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

import language_tool_python

tool = language_tool_python.LanguageTool('en-US')


# ─────────────────────────────────────────────────────────────────────────────
# Empathy phrase banks
# ─────────────────────────────────────────────────────────────────────────────

EMPATHY_OPENERS = [
    "i understand your concern",
    "i understand how frustrating",
    "i completely understand",
    "i sincerely apologize",
    "i apologize for the inconvenience",
    "i'm sorry to hear",
    "i'm sorry for",
    "thank you for bringing this to our attention",
    "thank you for reaching out",
    "thank you for contacting us",
    "i appreciate your patience",
    "we value your feedback",
    "we're sorry",
    "i hear you",
    "that must be frustrating",
    "i can imagine how",
    "i know this must be",
]

EMPATHY_PHRASES_TO_ADD = [
    "I understand your concern, and I'm here to help.",
    "I apologize for the inconvenience this has caused you.",
    "I completely understand how frustrating this must be.",
    "Thank you for bringing this to our attention.",
    "I appreciate your patience while we resolve this.",
]

HUMAN_OPENERS = [
    "I completely understand how frustrating this must be.",
    "I really understand your concern here.",
    "I’m sorry you had to face this issue.",
    "Thanks for bringing this to our attention.",
]

HUMAN_OWNERSHIP = [
    "Let me quickly check this for you.",
    "I’ll look into this right away.",
    "I’ll personally make sure this gets resolved.",
    "Let me take care of this for you.",
]

HUMAN_CLOSINGS = [
    "I’ll keep you updated on this.",
    "Thanks so much for your patience.",
    "I truly appreciate your understanding.",
    "I’ll make sure this is sorted out for you.",
]

# Keywords that signal a frustrated / upset customer message
FRUSTRATION_SIGNALS = [
    "not working", "doesn't work", "broken", "error", "issue", "problem",
    "frustrated", "angry", "upset", "disappointed", "terrible", "worst",
    "useless", "ridiculous", "unacceptable", "waiting", "still", "why",
    "horrible", "awful", "hate", "never", "always broken", "charged",
    "refund", "cancel", "complaint",
]

# Closing phrases that professional agents use
PROFESSIONAL_CLOSINGS = [
    "Please don't hesitate to reach out if you need further assistance.",
    "Is there anything else I can help you with today?",
    "Thank you for your patience, and we appreciate your business.",
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Grammar & Punctuation Correction  (rule-based; no external dependency)
# ─────────────────────────────────────────────────────────────────────────────

def _fix_capitalization(text: str) -> str:
    """Capitalize the first letter of every sentence."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    fixed = [s[0].upper() + s[1:] if s else s for s in sentences]
    return " ".join(fixed)


def _fix_spacing(text: str) -> str:
    """Remove double spaces and fix space-before-punctuation issues."""
    text = re.sub(r' {2,}', ' ', text)                   # collapse multiple spaces
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)          # remove space before punctuation
    text = re.sub(r'([,.!?;:])([^\s"\')])', r'\1 \2', text)  # ensure space after punctuation
    return text.strip()


def _ensure_sentence_ending(text: str) -> str:
    """Add a period if the text doesn't end with punctuation."""
    text = text.strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _fix_common_typos(text: str) -> Dict:
    """
    Rule-based replacement of extremely common typos / shorthand.
    Returns dict with 'fixed' text and list of 'errors' found.
    """
    corrections = {
        r"\bi\b": "I",               # lowercase i → I
        r"\bdont\b": "don't",
        r"\bcant\b": "can't",
        r"\bwont\b": "won't",
        r"\bisnt\b": "isn't",
        r"\barent\b": "aren't",
        r"\bwasnt\b": "wasn't",
        r"\bwerent\b": "weren't",
        r"\bhasnt\b": "hasn't",
        r"\bhavent\b": "haven't",
        r"\bwouldnt\b": "wouldn't",
        r"\bcouldnt\b": "couldn't",
        r"\bshouldnt\b": "shouldn't",
        r"\bim\b": "I'm",
        r"\bive\b": "I've",
        r"\bill\b": "I'll",
        r"\bId\b": "I'd",
        r"\bthru\b": "through",
        r"\bcoz\b": "because",
        r"\bcause\b": "because",
        r"\bu\b": "you",
        r"\bur\b": "your",
        r"\br\b": "are",
        r"\bpls\b": "please",
        r"\bplz\b": "please",
        r"\bthnks\b": "thanks",
        r"\bthx\b": "thanks",
        r"\basap\b": "as soon as possible",
        r"\bfyi\b": "for your information",
        r"\bbtw\b": "by the way",
        r"\bok\b": "okay",
    }
    errors = []
    for pattern, replacement in corrections.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and match.group() != replacement:
            errors.append({
                "original": match.group(),
                "suggestion": replacement,
                "rule": "Grammar / spelling correction",
            })
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return {"fixed": text, "errors": errors}


def correct_grammar(text: str) -> Dict:
    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)

    errors = []
    for m in matches:
        errors.append({
            "original": text[m.offset:m.offset + m.error_length],
            "suggestion": m.replacements[0] if m.replacements else "",
            "rule": m.ruleId
        })

    return {
        "corrected": corrected,
        "errors": errors
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Empathy Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_empathy(text: str) -> Dict:
    lower = text.lower()

    has_empathy = any(phrase in lower for phrase in EMPATHY_OPENERS)

    suggestion = "I understand your concern, and I'm here to assist you."

    empathy_score = 3 if has_empathy else 0

    return {
        "has_empathy": has_empathy,
        "empathy_score": empathy_score,
        "suggestion": suggestion,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tone Detection
# ─────────────────────────────────────────────────────────────────────────────

FORMAL_MARKERS = [
    "please", "kindly", "appreciate", "apologize", "sincerely",
    "assist", "resolve", "ensure", "inform", "regarding", "furthermore",
]
CASUAL_MARKERS = [
    "hey", "yeah", "yep", "nope", "gonna", "wanna", "gotta",
    "stuff", "kinda", "sorta", "awesome", "cool", "guys",
]


def detect_tone(text: str) -> str:
    """Returns 'Professional', 'Casual', or 'Neutral'."""
    lower = text.lower()
    formal_hits = sum(1 for m in FORMAL_MARKERS if m in lower)
    casual_hits = sum(1 for m in CASUAL_MARKERS if m in lower)

    if formal_hits > casual_hits:
        return "Professional"
    elif casual_hits > formal_hits:
        return "Casual"
    return "Neutral"


def detect_repetition(text: str):
    words = text.lower().split()
    seen = set()
    repeated = set()

    for word in words:
        if word in seen:
            repeated.add(word)
        else:
            seen.add(word)

    return list(repeated)


def detect_repeated_phrases(text: str):
    phrases = re.findall(r'\b\w+(?:\s+\w+){0,2}\b', text.lower())
    seen = set()
    duplicates = []

    for phrase in phrases:
        if phrase in seen:
            duplicates.append(phrase)
        else:
            seen.add(phrase)

    return duplicates


def is_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() > 0.7


def remove_repetition(text: str):
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    unique = []

    for s in sentences:
        if not any(is_similar(s.lower(), u.lower()) for u in unique):
            unique.append(s)

    return ". ".join(unique) + "."


def remove_over_apology(text: str):
    text = text.replace("I am really sorry. I am really sorry,", "I am really sorry,")
    text = text.replace("I'm really sorry. I'm really sorry,", "I'm really sorry,")
    return text


def final_cleanup(text: str) -> str:
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    unique = []

    for s in sentences:
        if s not in unique:
            unique.append(s)

    return ". ".join(unique) + "."


# ─────────────────────────────────────────────────────────────────────────────
# 4. Smart Response Improvement
# ─────────────────────────────────────────────────────────────────────────────

def improve_response(original: str, grammar_result: Dict, empathy_result: Dict) -> str:
    corrected = grammar_result["corrected"]
    lower = corrected.lower()

    parts = []

    # 🔹 1. Empathy (NOT always full sentence)
    if not empathy_result["has_empathy"]:
        empathy_options = [
            "I understand your concern.",
            "I’m really sorry about this.",
            "I understand how frustrating this must be.",
            ""  # sometimes skip for natural feel
        ]
        emp = random.choice(empathy_options)
        if emp:
            parts.append(emp)

    # 🔹 2. Main message (keep it simple)
    parts.append(corrected)

    # 🔹 3. Ownership (short + natural)
    if not any(x in lower for x in ["i will", "let me", "i'll"]):
        ownership_options = [
            "Let me check that for you.",
            "I’ll check this and update you.",
            "Give me a moment, I’ll look into it.",
            ""  # sometimes skip
        ]
        own = random.choice(ownership_options)
        if own:
            parts.append(own)

    # 🔹 4. Closing (ONLY sometimes)
    closing_options = [
        "",
        "Thanks for your patience.",
        "Appreciate your understanding.",
    ]
    close = random.choice(closing_options)
    if close:
        parts.append(close)

    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Quality Scoring  (out of 10)
# ─────────────────────────────────────────────────────────────────────────────

def compute_score(text: str, grammar_errors: List, empathy_result: Dict) -> Dict:
    """
    Scoring breakdown (10 points total):
      Grammar clarity   : 4 pts  (−0.5 per error, min 0)
      Empathy presence  : 3 pts
      Length adequacy   : 2 pts  (penalise very short responses)
      Professional tone : 1 pt
    """
    # Grammar sub-score
    grammar_pts = max(0.0, 4.0 - len(grammar_errors) * 0.5)

    # Empathy sub-score
    empathy_pts = float(empathy_result["empathy_score"])  # 0 or 3

    # Length sub-score
    word_count = len(text.split())
    if word_count >= 15:
        length_pts = 2.0
    elif word_count >= 8:
        length_pts = 1.0
    else:
        length_pts = 0.0

    # Tone sub-score
    tone = detect_tone(text)
    tone_pts = 1.0 if tone == "Professional" else 0.5 if tone == "Neutral" else 0.0

    total = grammar_pts + empathy_pts + length_pts + tone_pts
    total = min(10.0, round(total, 1))

    return {
        "total": total,
        "breakdown": {
            "grammar": round(grammar_pts, 1),
            "empathy": round(empathy_pts, 1),
            "length": round(length_pts, 1),
            "tone": round(tone_pts, 1),
        },
        "label": _score_label(total),
    }


def _score_label(score: float) -> str:
    if score >= 8.5:
        return "Excellent"
    elif score >= 7:
        return "Good"
    elif score >= 5:
        return "Needs Improvement"
    else:
        return "Poor"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Public API — single entry-point used by routes.py
# ─────────────────────────────────────────────────────────────────────────────

def analyze(text: str) -> Dict:
    """
    Master function — runs the full pipeline and returns a unified JSON-ready dict.
    """
    if not text or not text.strip():
        return {
            "original": text,
            "corrected": "",
            "improved": "",
            "score": {"total": 0, "breakdown": {}, "label": "Poor"},
            "grammar_errors": [],
            "empathy": {"has_empathy": False, "suggestion": ""},
            "tone": "Neutral",
            "highlights": [],
        }

    # Step 1: remove repetition + over apology
    cleaned_text = remove_repetition(text)
    cleaned_text = remove_over_apology(cleaned_text)

    # Step 2: grammar
    grammar_result = correct_grammar(cleaned_text)

    # Step 3: empathy
    empathy_result = detect_empathy(cleaned_text)

    # Step 4: FINAL IMPROVEMENT (use CLEAN text only)
    improved = improve_response(cleaned_text, grammar_result, empathy_result)
    improved = final_cleanup(improved)

    # Step 5: Detect repetition for UI display
    repeats = detect_repeated_phrases(text)

    repetition_errors = [
        {
            "original": r,
            "suggestion": "Avoid repeating the same phrase",
            "rule": "Repetition detected"
        }
        for r in repeats
    ]

    # Step 6: Merge errors
    all_errors = grammar_result["errors"] + repetition_errors

    tone = detect_tone(cleaned_text)
    score = compute_score(cleaned_text, all_errors, empathy_result)

    return {
        "original": text,
        "corrected": grammar_result["corrected"],
        "improved": improved,
        "score": score,
        "grammar_errors": all_errors,
        "empathy": {
            "has_empathy": empathy_result["has_empathy"],
            "suggestion": empathy_result["suggestion"],
        },
        "tone": tone,
    }
