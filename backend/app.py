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
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
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
    print("Saving emotion:", emotion)

    history: list = [] # Initialize history as an empty list by default

    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            print(f"Could not load history from {HISTORY_PATH}, starting new: {exc}")
            history = [] # Reset history if file is corrupt or unreadable

    history.append({
        "emotion": emotion,
        "time": datetime.datetime.now().isoformat(),
    })

    print(f"History length after saving: {len(history)}")

    try:
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)
    except OSError as exc:
        # Don't let a history write failure break the main response
        print(f"Could not save history to {HISTORY_PATH}: {exc}")


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

def generate_companion_steps(emotion: str) -> list[str]:
    """Return dynamic, grounding messages for AI Companion Mode based on emotion."""
    if emotion == "anxiety":
        return [
            "Stay here with me.",
            "You're safe right now.",
            "Put your feet firmly on the ground.",
            "Press your hands together for 5 seconds.",
            "Now slowly exhale.",
            "Keep your focus here."
        ]
    elif emotion == "anger":
        return [
            "I can feel the intensity.",
            "Clench your fists tightly.",
            "Hold... and release.",
            "Let that energy move out.",
            "Slow your breathing."
        ]
    elif emotion == "freeze":
        return [
            "You're not stuck, just paused.",
            "Move your fingers slowly.",
            "Now your shoulders.",
            "Stand up if you can.",
            "Shake your arms gently."
        ]
    elif emotion == "sadness":
        return [
            "I'm here with you.",
            "It's okay to feel heavy right now.",
            "Place one hand on your chest.",
            "Feel the warmth of your hand.",
            "Take a slow, gentle breath."
        ]
    else:
        return [
            "Let's take a moment together.",
            "Notice your breathing.",
            "Allow your shoulders to drop.",
            "You are doing okay."
        ]

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
    if err or not message:
        return err

    regulation_map = load_regulation_map()

    intensity = "high" if len(str(message).split()) > 12 else "low"

    # --- Personalization Logic ---
    history = load_history()
    last_emotion = history[-1]["emotion"] if history else None

    dominant_emotion = None
    if history:
        emotion_count = {}
        for entry in history:
            e = entry["emotion"]
            emotion_count[e] = emotion_count.get(e, 0) + 1
        if emotion_count:
            dominant_emotion = max(emotion_count, key=lambda e: emotion_count.get(e, 0))

    emotion = detect_emotion(str(message))
    
    insight_hint = ""
    # We only show hints on non-neutral real emotions
    if emotion not in ["neutral", "critical"]:
        if emotion == last_emotion:
            insight_hint = "You're experiencing this repeatedly. Let's intervene earlier this time."
        elif emotion == dominant_emotion:
            insight_hint = "This seems like a recurring pattern. Let's slow it down early."

    # --- Early Warning System (Pre-Trigger Detection) ---
    current_hour = datetime.datetime.now().hour
    current_time_bucket = "night"
    if 6 <= current_hour < 12:
        current_time_bucket = "morning"
    elif 12 <= current_hour < 17:
        current_time_bucket = "afternoon"
    elif 17 <= current_hour < 21:
        current_time_bucket = "evening"

    pre_trigger_alert = None
    if history and len(history) > 3:
        time_patterns = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        for entry in history:
            try:
                dt = datetime.datetime.fromisoformat(entry["time"])
                hr = dt.hour
                if 6 <= hr < 12: time_patterns["morning"] += 1
                elif 12 <= hr < 17: time_patterns["afternoon"] += 1
                elif 17 <= hr < 21: time_patterns["evening"] += 1
                else: time_patterns["night"] += 1
            except Exception:
                pass
        
        peak_time_key = max(time_patterns, key=lambda k: time_patterns.get(k, 0))
        if current_time_bucket == peak_time_key and time_patterns[peak_time_key] > 0:
            pre_trigger_alert = f"You might feel more tense during the {current_time_bucket}. Let's stabilize early."

    # Safety check — highest priority
    if is_crisis(message):
        result = regulation_map["critical"]
        return jsonify({
            "emotion": "critical",
            "intensity": intensity,
            "pre_trigger_alert": pre_trigger_alert,
            "insight_hint": insight_hint,
            "body_state": result["body_state"],
            "action": result["action"],
        }), 200

    save_history(emotion)

    if intensity == "high" and emotion != "critical":
        return jsonify({
            "emotion": emotion,
            "intensity": intensity,
            "mode": "companion",
            "pre_trigger_alert": pre_trigger_alert,
            "insight_hint": insight_hint,
            "messages": generate_companion_steps(emotion)
        }), 200

    regulation = regulation_map.get(emotion, regulation_map["neutral"])

    return jsonify({
        "emotion": emotion,
        "intensity": intensity,
        "pre_trigger_alert": pre_trigger_alert,
        "insight_hint": insight_hint,
        "body_state": regulation["body_state"],
        "action": regulation["action"],
    }), 200


@app.route("/insights", methods=["GET"])
def insights():
    default_empty = {
        "total_entries": 0, 
        "dominant_emotion": "neutral", 
        "emotion_breakdown": {}, 
        "insight": "No data yet.",
        "time_patterns": {"morning": 0, "afternoon": 0, "evening": 0, "night": 0},
        "prediction": "No clear patterns yet."
    }

    if not os.path.exists(HISTORY_PATH):
        return jsonify(default_empty), 200

    try:
        with open(HISTORY_PATH, "r") as f:
            history = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return jsonify(default_empty), 200

    total_entries = len(history)
    if total_entries == 0:
        return jsonify(default_empty), 200

    emotion_count = {}
    time_patterns = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
    
    for entry in history:
        e = entry["emotion"]
        emotion_count[e] = emotion_count.get(e, 0) + 1
        
        try:
            # Parse ISO time
            dt = datetime.datetime.fromisoformat(entry["time"])
            hr = dt.hour
            if 6 <= hr < 12:
                time_patterns["morning"] += 1
            elif 12 <= hr < 17:
                time_patterns["afternoon"] += 1
            elif 17 <= hr < 21:
                time_patterns["evening"] += 1
            else:
                time_patterns["night"] += 1
        except Exception:
            pass

    dominant_emotion = max(emotion_count, key=lambda e: emotion_count.get(e, 0))
    
    peak_time_key = max(time_patterns, key=lambda k: time_patterns.get(k, 0))
    if time_patterns[peak_time_key] > 0 and dominant_emotion not in ["neutral", "critical"]:
        prediction = f"You often feel {dominant_emotion} during the {peak_time_key}."
    elif time_patterns[peak_time_key] > 0:
        prediction = f"Your logs usually happen during the {peak_time_key}."
    else:
        prediction = "No clear time patterns yet."
    
    insight_messages = {
        "anxiety": "You've been feeling anxious frequently. Try slowing down your breathing.",
        "anger": "There’s a pattern of frustration. Releasing tension physically might help.",
        "freeze": "You seem stuck or low-energy often. Gentle movement can help reset.",
        "sadness": "You've been feeling low. Try grounding yourself with small actions.",
        "neutral": "Your state seems balanced.",
        "critical": "You are experiencing high distress. Please continue to reach out for support."
    }
    
    insight = insight_messages.get(dominant_emotion, "Your state seems balanced.")

    return jsonify({
        "total_entries": total_entries,
        "dominant_emotion": dominant_emotion,
        "emotion_breakdown": emotion_count,
        "insight": insight,
        "time_patterns": time_patterns,
        "prediction": prediction
    }), 200


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
