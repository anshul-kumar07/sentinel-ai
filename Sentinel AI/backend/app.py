import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_urls(text):
    url_pattern = r'(https?://\S+|www\.\S+)'
    return re.findall(url_pattern, text)

# ===== ADD (CORS PREFLIGHT – ESSENTIAL) =====
@app.route("/analyze", methods=["OPTIONS"])
def analyze_options():
    return "", 200

@app.route("/analyze-image", methods=["OPTIONS"])
def analyze_image_options():
    return "", 200
# ===========================================


# ---------------- HELPERS ----------------

def extract_domain(text):
    match = re.search(r"https?://([^/\s]+)", text)
    return match.group(1).lower() if match else None


def is_suspicious_domain(domain):
    reasons = []

    suspicious_words = [
        "login", "secure", "verify", "career",
        "support", "account", "update", "portal"
    ]

    cheap_tlds = [".info", ".xyz", ".top", ".site", ".online"]

    if "-" in domain:
        reasons.append("Uses hyphenated domain structure")

    if any(word in domain for word in suspicious_words):
        reasons.append("Contains impersonation-related keywords")

    if any(domain.endswith(tld) for tld in cheap_tlds):
        reasons.append("Uses low-trust domain extension")

    if len(domain) > 25:
        reasons.append("Unusually long domain name")

    return reasons


def analyze_message_text(message):
    message = message.lower()

    explanations = []
    score = 0

    # DOMAIN CHECK
    domain = extract_domain(message)
    if domain:
        domain_flags = is_suspicious_domain(domain)
        if domain_flags:
            score += 30
            explanations.append({
                "title": "Suspicious Link Detected",
                "text": f"The link ({domain}) shows patterns commonly used in phishing scams."
            })
            for reason in domain_flags:
                explanations.append({
                    "title": "Domain Analysis",
                    "text": reason
                })

    # URGENCY
    urgency_words = ["urgent","limited slots" , "immediately", "today", "last chance", "suspended"]
    if any(word in message for word in urgency_words):
        score += 20
        explanations.append({
            "title": "Urgency Pressure",
            "text": "The message pressures you to act quickly without verification."
        })

    # PAYMENT
    payment_words = ["pay", "fee", "deposit", "registration", "processing"]
    if any(word in message for word in payment_words):
        score += 25
        if score < 30:
         explanations = [
        {
            "title": "Verified Domain",
            "text": "The message links to an official and trusted organization domain."
        },
        {
            "title": "No Urgency Detected",
            "text": "The message does not pressure the recipient to act immediately."
        },
        {
            "title": "No Payment Request",
            "text": "There is no request for upfront payment or sensitive financial information."
        },
        {
            "title": "Professional Communication",
            "text": "The message follows a standard professional communication pattern."
        }
    ]


    # IDENTITY
    if "@" not in message and "official" not in message:
        score += 10
        explanations.append({
            "title": "Unverified Sender Identity",
            "text": "No official sender identity is provided."
        })

    # FINAL RISK
    if score >= 60:
        risk = "High"
    elif score >= 30:
        risk = "Medium–High"
    else:
        risk = "Low"

    if not explanations:
        explanations.append({
            "title": "No Strong Scam Indicators",
            "text": "The message does not show clear scam patterns."
        })

    return {
        "overall_risk": risk,
        "confidence_score": score,
        "analysis": explanations,
        "recommendation":
            "Only interact through verified official websites."
            if risk != "Low"
            else "No immediate action required."
    }

# ---------------- MAIN API ----------------

@app.route("/analyze", methods=["POST"])
def analyze_message():
    # ===== ADD (SAFE JSON – ESSENTIAL) =====
    data = request.get_json(silent=True) or {}
    # ======================================

    message = data.get("message", "").lower()

    explanations = []
    score = 0

    # 1️⃣ DOMAIN INTELLIGENCE
    domain = extract_domain(message)
    if not domain:
    explanations.append({
        "title": "No Domain Found",
        "text": "No website link was detected in this message."
    })

    if domain:
        flags = is_suspicious_domain(domain)
        if flags:
            score += 30
            explanations.append({
                "title": "Suspicious Link Detected",
                "text": f"The link ({domain}) shows patterns commonly used in phishing scams."
            })
            for reason in flags:
                explanations.append({
                    "title": "Domain Analysis",
                    "text": reason
                })

    # 2️⃣ URGENCY
    urgency_words = ["urgent", "limited slots" , "immediately", "suspended", "blocked", "today"]
    if any(word in message for word in urgency_words):
        score += 20
        explanations.append({
            "title": "Urgency Pressure",
            "text": "The message pressures you to act quickly without verification."
        })

    # PAYMENT REQUEST
payment_words = ["pay", "fee", "deposit", "registration", "processing"]

if any(word in message for word in payment_words):
    score += 25
    explanations.append({
        "title": "Payment Request Detected",
        "text": "The message asks for money which is a common scam pattern."
    })

    # 4️⃣ IDENTITY WEAKNESS
    if "@" not in message and "official" not in message:
     score += 10

    explanations.append({
        "title": "No Strong Scam Indicators",
        "text": "This message appears legitimate based on current analysis."
    })

    explanations.append({
        "title": "Unverified Sender Identity",
        "text": "No official sender identity is provided."
    })


    # ---------- FINAL RISK ----------
    if score >= 60:
        risk = "High"
    elif score >= 25:
        risk = "Medium–High"
    elif score >= 20:
        risk = "Low–Medium"
    else:
        risk = "Low"

    if not explanations:
        explanations.append({
            "title": "No Strong Scam Indicators",
            "text": "The message does not show clear scam patterns."
        })

    return jsonify({
        "overall_risk": risk,
        "confidence_score": score,
        "analysis": explanations,
        "recommendation":
            "Only interact through verified official websites."
            if risk != "Low"
            else "No immediate action required."
    })

from PIL import Image
import pytesseract

def extract_text_from_image(image_file):
    img = Image.open(image_file)
    text = pytesseract.image_to_string(img)
    return text.strip()

@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    image = request.files.get("image")

    if not image:
        return jsonify({"error": "No image uploaded"}), 400

    extracted_text = extract_text_from_image(image)

    if not extracted_text:
        return jsonify({
            "extracted_text": "",
            "overall_risk": "Low",
            "analysis": [{
                "title": "No readable text detected",
                "text": "The uploaded image does not contain readable text."
            }],
            "recommendation": "Ensure the image is clear and readable."
        })

    # ✅ REUSE TEXT ANALYSIS
    result = analyze_message_text(extracted_text)

    # ✅ ATTACH OCR TEXT FOR UI
    result["extracted_text"] = extracted_text

    return jsonify(result)

import os
@app.route("/")
def home():
    return "Sentinel backend running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)






