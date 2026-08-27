# app.py - main flask server for ctrl+fly
# ye 2 kaam karta hai: 1) poori website serve karta hai (html/css/js)
# 2) telemetry ke liye kuch api routes deta hai jo telemetry.html use karta hai
#
# run karne ke liye:
#   pip install -r backend/requirements.txt
#   python backend/app.py
# fir browser me http://127.0.0.1:5000 khol lena

import os
from flask import Flask, request, jsonify, send_from_directory, Response

import telemetry_engine as te

# project ka root folder (backend/ ke ek level upar, jaha index.html hai)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")

# bas ek simple dict me current flight rakh rha hu, database jaisa kuch nahi
# (single user demo ke liye enough hai)
STATE = {"records": [], "encrypted": None}


# home page serve karna

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


# quick health check

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "records_loaded": len(STATE["records"])})


# ek sample flight generate karo (zone/level/duration lekar)

@app.route("/api/telemetry/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    zone = data.get("zone", "Desert Basin")
    level = int(data.get("level", 1))
    duration = int(data.get("duration", 60))

    records = te.generate_sample_flight(zone=zone, level=level, duration_s=duration)
    STATE["records"] = records
    STATE["encrypted"] = None

    return jsonify({"zone": zone, "level": level, "count": len(records), "records": records})


# current flight ko encrypt kar do (demo cipher, upar telemetry_engine me note likha hai)

@app.route("/api/telemetry/encrypt", methods=["POST"])
def encrypt():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")

    if not STATE["records"]:
        return jsonify({"error": "No flight loaded yet. Generate or upload one first."}), 400
    if not password:
        return jsonify({"error": "A password is required to encrypt."}), 400

    blob = te.encrypt_records(STATE["records"], password)
    STATE["encrypted"] = blob
    return jsonify({"size_bytes": len(blob)})


@app.route("/api/telemetry/encrypted.bin")
def download_encrypted():
    if not STATE["encrypted"]:
        return jsonify({"error": "Nothing has been encrypted yet."}), 400
    return Response(
        STATE["encrypted"],
        mimetype="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=flight_record.enc"},
    )


# decrypt + validate - ya to upload ki hui .enc file ya jo abhi memory me hai

@app.route("/api/telemetry/validate", methods=["POST"])
def validate():
    uploaded_file = request.files.get("file")
    if uploaded_file:
        password = request.form.get("password")
    else:
        password = (request.get_json(silent=True) or {}).get("password")

    if uploaded_file:
        blob = uploaded_file.read()
    elif STATE["encrypted"]:
        blob = STATE["encrypted"]
    else:
        return jsonify({"error": "No encrypted flight record available. Encrypt one first, or upload a .enc file."}), 400

    if not password:
        return jsonify({"error": "A password is required to decrypt."}), 400

    try:
        records = te.decrypt_records(blob, password)
    except Exception:
        return jsonify({"error": "Decryption failed — wrong password, or the file is corrupted."}), 400

    report = te.validate_records(records)
    STATE["records"] = records
    return jsonify({"report": report, "records": records})


# apni khud ki plain csv upload karke validate karwana

@app.route("/api/telemetry/upload-csv", methods=["POST"])
def upload_csv():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return jsonify({"error": "No file uploaded."}), 400

    text = uploaded_file.read().decode("utf-8", errors="replace")
    records = te.parse_uploaded_csv(text)
    report = te.validate_records(records)
    STATE["records"] = records
    return jsonify({"report": report, "records": records})


# current flight ko csv/kml me export karna

@app.route("/api/telemetry/csv")
def export_csv():
    if not STATE["records"]:
        return jsonify({"error": "No flight loaded yet."}), 400
    csv_text = te.to_csv_string(STATE["records"])
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=flight_track.csv"},
    )


@app.route("/api/telemetry/kml")
def export_kml():
    if not STATE["records"]:
        return jsonify({"error": "No flight loaded yet."}), 400
    kml_text = te.to_kml_string(STATE["records"])
    return Response(
        kml_text,
        mimetype="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": "attachment; filename=flight_track.kml"},
    )


if __name__ == "__main__":
    # agar 5000 already busy hai (mac pe aksar hota hai) to yaha port change kar dena
    app.run(debug=True, port=5000)
