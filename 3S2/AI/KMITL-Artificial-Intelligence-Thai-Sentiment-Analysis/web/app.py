import os
import re
import json
import io
import emoji
import joblib

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file
)
from pythainlp.tokenize import word_tokenize
from scipy.sparse import hstack

# =========================
# Flask setup
# =========================
app = Flask(__name__, template_folder="template", static_folder="static")

# =========================
# Tokenizer (MUST exist before loading TF-IDF)
# =========================
def thai_tokenizer(text):
    return word_tokenize(text, engine="newmm")


def clean_text(text):
    text = str(text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'http\S+|www\S+', ' <URL> ', text)
    text = re.sub(r'@\S+', ' <USER> ', text)
    text = emoji.replace_emoji(text, replace=' <EMOJI> ')
    text = re.sub(r'[^ก-๙a-zA-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# =========================
# Load models
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

model = joblib.load(os.path.join(MODEL_DIR, "lgb_model.pkl"))
tfidf_word = joblib.load(os.path.join(MODEL_DIR, "tfidf_word.pkl"))
tfidf_char = joblib.load(os.path.join(MODEL_DIR, "tfidf_char.pkl"))
le = joblib.load(os.path.join(MODEL_DIR, "label_encoder.pkl"))


# =========================
# Prediction logic
# =========================
def predict_sentiment(text):
    text = clean_text(text)

    Xw = tfidf_word.transform([text])
    Xc = tfidf_char.transform([text])
    X = hstack([Xw, Xc])

    pred = model.predict(X)
    label = le.inverse_transform(pred)[0]

    confidence = None
    if hasattr(model, "predict_proba"):
        confidence = float(model.predict_proba(X).max())

    return label, confidence


# =========================
# Routes
# =========================

# ---- Serve HTML ----
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# ---- Single text prediction (JSON) ----
@app.route("/", methods=["POST"])
def predict_single():
    if not request.is_json:
        return jsonify({"error": "JSON body required"}), 400

    data = request.get_json()
    if "prompt" not in data:
        return jsonify({"error": "missing 'prompt' field"}), 400

    label, confidence = predict_sentiment(data["prompt"])

    return jsonify({
        "sentiment": label,
        "confidence": confidence
    })


# ---- Upload JSON → fill sentiment → DOWNLOAD JSON ----
@app.route("/api/upload_json", methods=["POST"])
def upload_json():
    if "file" not in request.files:
        return jsonify({"error": "no file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.lower().endswith(".json"):
        return jsonify({"error": "only .json files allowed"}), 400

    try:
        data = json.loads(file.read().decode("utf-8"))
    except Exception as e:
        return jsonify({"error": "invalid json", "detail": str(e)}), 400

    if "text" not in data:
        return jsonify({"error": "json must contain 'text' field"}), 400

    # Keep or create sentiment field
    sentiments = data.get("sentiment", {})

    for key, text in data["text"].items():
        label, _ = predict_sentiment(text)
        sentiments[key] = label

    # Fill sentiment back into original structure
    data["sentiment"] = sentiments

    # Create downloadable JSON
    buffer = io.BytesIO()
    buffer.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/json",
        as_attachment=True,
        download_name="filled_sentiment.json"
    )


# =========================
# Run app
# =========================
if __name__ == "__main__":
    app.run(debug=True)
