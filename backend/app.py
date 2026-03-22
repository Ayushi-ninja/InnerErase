# -----------------------------------------------
# InnerEase AI — Flask Backend
# POST /analyze endpoint
# -----------------------------------------------

import json
import os
import re
import logging
import datetime
from functools import lru_cache
from flask import Flask, request, jsonify, g
from flask_cors import CORS

# -----------------------------------------------
# App setup
# -----------------------------------------------
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------
# Paths
# -----------------------------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data", "regulation_map.json")
HISTORY_PATH = os.path.join(BASE_DIR, "data", "history.json")

# -----------------------------------------------
# Load regulation map once at startup (not per request)
# -----------------------------------------------
@lru_cache(maxsize=1)
def load_regulation_map() -> dict:
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# -----------------------------------------------
# Crisis keywords — pre-compiled for speed
# -----------------------------------------------
CRISIS_PATTERN = re.compile(
    r"\b("
    r"want to die|kill myself|end my life|hurt myself|self[\s-]?harm"
    r"|can'?t live|no reason to live|suicidal|suicide"
    r")\b",
    re.IGNORECASE,
)

# -----------------------------------------------
# Emotion keyword map — phrase-first ordering
# so multi-word phrases are matched before single words
# -----------------------------------------------
EMOTION_KEYWORDS: dict[str, list[str]] = {
    "anxiety": [
        "can't breathe", "heart racing",         # phrases first (weight ×2)
        "anxious", "anxiety", "overwhelmed", "panicking", "panic",
        "nervous", "worried", "worry", "scared", "fear", "tense", "restless",
    ],
    "anger": [
        "furious", "rage",                        # phrases first
        "angry", "anger", "irritated", "frustrated",
        "mad", "annoyed", "hateful", "explosive", "snapping",
    ],
    "sadness": [
        "heartbroken", "devastated", "miserable", # phrases first
        "sad", "sadness", "cry", "crying", "hopeless", "depressed",
        "grief", "empty", "lost", "lonely", "numb",
    ],
    "freeze": [
        "can't move", "cannot move", "zoned out",  # phrases first
        "shut down", "spacing out", "dissociated",
        "freeze", "frozen", "stuck", "paralyzed", "disconnected", "blank",
    ],
}

# Pre-compile each keyword as a whole-word regex for precision
_EMOTION_PATTERNS: dict[str, list[tuple[re.Pattern, int]]] = {}
for _emotion, _keywords in EMOTION_KEYWORDS.items():
    _EMOTION_PATTERNS[_emotion] = []
    for kw in _keywords:
        weight = 2 if len(kw.split()) > 1 else 1
        pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
        _EMOTION_PATTERNS[_emotion].append((pattern, weight))

# -----------------------------------------------
# Helpers
# -----------------------------------------------

def is_crisis(message: str) -> bool:
    return bool(CRISIS_PATTERN.search(message))


def detect_emotion(message: str) -> str:
    scores: dict[str, int] = {emotion: 0 for emotion in _EMOTION_PATTERNS}

    for emotion, patterns in _EMOTION_PATTERNS.items():
        for pattern, weight in patterns:
            if pattern.search(message):
                scores[emotion] += weight

    best_emotion = max(scores, key=scores.get)
    return best_emotion if scores[best_emotion] > 0 else "neutral"


def save_history(emotion: str) -> None:
    """Append an emotion event to history.json (creates file if missing)."""
    try:
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r") as f:
                history: list = json.load(f)
        else:
            history = []

        history.append({
            "emotion": emotion,
            "time": datetime.datetime.utcnow().isoformat() + "Z",
        })

        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)

    except (OSError, json.JSONDecodeError) as exc:
        # Don't let a history write failure break the main response
        logger.warning("Could not save history: %s", exc)


def load_history() -> list:
    """Return history list; empty list if file is missing or corrupt."""
    try:
        if not os.path.exists(HISTORY_PATH):
            return []
        with open(HISTORY_PATH, "r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load history: %s", exc)
        return []

# -----------------------------------------------
# Request validation helper
# -----------------------------------------------
def parse_message() -> tuple[str | None, tuple | None]:
    """
    Parse and validate the incoming JSON body.
    Returns (message, None) on success or (None, error_response) on failure.
    """
    data = request.get_json(silent=True)
    if not data:
        return None, (jsonify({"error": "Request body must be JSON"}), 400)
    message = data.get("message", "").strip()
    if not message:
        return None, (jsonify({"error": "Message is required"}), 400)
    return message, None

# -----------------------------------------------
# Routes
# -----------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    message, err = parse_message()
    if err:
        return err

    regulation_map = load_regulation_map()

    # Safety check — highest priority
    if is_crisis(message):
        result = regulation_map["critical"]
        return jsonify({
            "emotion": "critical",
            "body_state": result["body_state"],
            "action": result["action"],
        }), 200

    emotion = detect_emotion(message)
    save_history(emotion)

    regulation = regulation_map.get(emotion, regulation_map["neutral"])

    return jsonify({
        "emotion": emotion,
        "body_state": regulation["body_state"],
        "action": regulation["action"],
    }), 200


@app.route("/insights", methods=["GET"])
def insights():
    history = load_history()

    emotion_count: dict[str, int] = {}
    for entry in history:
        e = entry.get("emotion", "unknown")
        emotion_count[e] = emotion_count.get(e, 0) + 1

    return jsonify(emotion_count), 200


# -----------------------------------------------
# Global error handler
# -----------------------------------------------
@app.errorhandler(Exception)
def handle_error(exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return jsonify({"error": "Something went wrong"}), 500


# -----------------------------------------------
# Entry point
# -----------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
