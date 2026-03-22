# API Contract — InnerEase AI

## Base URL

http://127.0.0.1:5000

---

## 📌 Endpoint: Analyze Emotion

### POST /analyze

---

## 📨 Request

### Headers:

Content-Type: application/json

### Body:

{
"message": "I feel anxious and overwhelmed"
}

---

## 📤 Response (Success)

Status: 200 OK

{
"emotion": "anxiety",
"body_state": "tight chest, fast breathing",
"action": "inhale for 4 seconds, exhale for 6 seconds (repeat 5 times)"
}

---

## ⚠️ Error Responses

### 400 Bad Request

{
"error": "Message is required"
}

---

### 500 Internal Server Error

{
"error": "Something went wrong"
}

---

## 🚨 Safety Response (Critical Case)

If input contains:

* self-harm intent
* suicidal thoughts
* crisis language

Return:

{
"emotion": "critical",
"body_state": "high distress",
"action": "You are not alone. Please consider reaching out to a trusted person or a local helpline immediately."
}

---

## 🧠 Notes

* Emotion must be one of:

  * anxiety
  * anger
  * sadness
  * freeze
  * neutral

* Response must be:

  * short
  * clear
  * actionable

* Do NOT return long paragraphs

---

## 🔄 Future Extensions (Not MVP)

* /history
* /patterns
* /voice-input
* /user-profile
