# telemetry_engine.py
# yahi pe saara telemetry ka logic hai - sample flight banana, csv padhna,
# validate karna, csv/kml me export karna aur encrypt/decrypt karna
#
# encryption wala part simple XOR cipher hai (password se hash banake keystream
# nikal ke xor kar deta hu). ye real security ke liye nahi hai, bas ye dikhane
# ke liye ki encrypted flight record ko decrypt+validate kaise karte hai.
# agar kabhi actual product banana ho to "cryptography" wali library use karna,
# uska Fernet already secure hai.

import base64
import csv
import hashlib
import io
import json
import math
import random

# ---- 1. sample flight banane ka part ----

ZONE_ORIGINS = {
    "Desert Basin":  (26.9124, 75.7873),
    "Metro Skyline": (28.6139, 77.2090),
    "Arctic Ridge":  (78.2232, 15.6267),
    "Ocean Platform": (19.0760, 72.8777),
}

LEVEL_ALT_RANGE = {1: (40, 90), 2: (120, 220), 3: (260, 420)}


def _format_ts(t_seconds):
    m = int(t_seconds // 60)
    s = t_seconds - m * 60
    return f"00:{m:02d}:{s:04.1f}"


def generate_sample_flight(zone="Desert Basin", level=1, duration_s=60,
                            interval_s=4, seed=None):
    """Simulate a plausible drone flight log for demo/testing purposes."""
    rng = random.Random(seed)
    lat, lon = ZONE_ORIGINS.get(zone, ZONE_ORIGINS["Desert Basin"])
    alt_lo, alt_hi = LEVEL_ALT_RANGE.get(int(level), LEVEL_ALT_RANGE[1])

    records = []
    t = 0.0
    battery = 16.8
    heading = rng.uniform(0, 360)

    while t <= duration_s:
        climb = min(1.0, t / max(6.0, duration_s * 0.15))
        alt = max(0.0, (alt_lo + (alt_hi - alt_lo) * climb) * (0.9 + 0.1 * math.sin(t / 9)))
        speed = max(0.0, 8 + (alt_hi / 10) * climb + rng.uniform(-1.5, 1.5))
        heading = (heading + rng.uniform(-6, 6)) % 360
        lat += math.cos(math.radians(heading)) * 0.00006 * (speed / 20)
        lon += math.sin(math.radians(heading)) * 0.00006 * (speed / 20)
        battery = max(9.5, battery - 0.006 * interval_s)

        records.append({
            "timestamp": _format_ts(t),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "alt_m": round(alt, 1),
            "speed_kmh": round(speed, 1),
            "heading": round(heading, 1),
            "battery_v": round(battery, 2),
            "sats": rng.randint(8, 12),
        })
        t += interval_s

    return records


# ---- 2. apni khud ki csv upload ki hui parse karna ----


COLUMN_ALIASES = {
    "timestamp": ["timestamp", "time", "ts"],
    "lat": ["lat", "latitude"],
    "lon": ["lon", "lng", "longitude"],
    "alt_m": ["alt_m", "altitude", "alt"],
    "speed_kmh": ["speed_kmh", "speed", "spd"],
    "heading": ["heading", "hdg", "bearing"],
    "battery_v": ["battery_v", "battery", "voltage"],
    "sats": ["sats", "satellites", "gps_sats"],
}


def _find_col(headers, aliases):
    lower = {h.strip().lower(): h for h in headers}
    for a in aliases:
        if a in lower:
            return lower[a]
    return None


def parse_uploaded_csv(file_text):
    """Best-effort parse of an arbitrary drone-log CSV into our record schema."""
    reader = csv.DictReader(io.StringIO(file_text))
    headers = reader.fieldnames or []
    colmap = {field: _find_col(headers, aliases) for field, aliases in COLUMN_ALIASES.items()}

    records = []
    for i, row in enumerate(reader):
        rec = {"timestamp": row.get(colmap["timestamp"]) if colmap["timestamp"] else f"row-{i}"}
        for field in ["lat", "lon", "alt_m", "speed_kmh", "heading", "battery_v", "sats"]:
            col = colmap[field]
            rec[field] = row.get(col) if col else None
        records.append(rec)
    return records


# ---- 3. validation - basic sanity checks ----


def validate_records(records):
    issues = []
    for i, r in enumerate(records):
        try:
            lat = float(r.get("lat"))
            lon = float(r.get("lon"))
            alt = float(r.get("alt_m"))
            spd = float(r.get("speed_kmh"))
            batt = float(r.get("battery_v"))
            sats = int(float(r.get("sats") or 0))
        except (TypeError, ValueError):
            issues.append({"row": i, "reason": "non-numeric or missing field"})
            continue

        if not (-90 <= lat <= 90):
            issues.append({"row": i, "reason": f"latitude out of range ({lat})"})
        if not (-180 <= lon <= 180):
            issues.append({"row": i, "reason": f"longitude out of range ({lon})"})
        if alt < 0:
            issues.append({"row": i, "reason": f"negative altitude ({alt})"})
        if spd < 0 or spd > 400:
            issues.append({"row": i, "reason": f"speed out of range ({spd})"})
        if batt < 5 or batt > 30:
            issues.append({"row": i, "reason": f"battery voltage out of range ({batt})"})
        if sats < 0:
            issues.append({"row": i, "reason": f"invalid satellite count ({sats})"})

    bad_rows = {issue["row"] for issue in issues}
    return {
        "total_records": len(records),
        "valid_records": len(records) - len(bad_rows),
        "flagged_records": len(bad_rows),
        "issues": issues[:50],  # cap payload size
    }


# ---- 4. encrypt/decrypt (simple, demo only, see comment upar) ----


def _keystream(password, length):
    key = hashlib.sha256(password.encode("utf-8")).digest()
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hashlib.sha256(key + counter.to_bytes(4, "big")).digest())
        counter += 1
    return bytes(out[:length])


def encrypt_records(records, password):
    payload = json.dumps(records).encode("utf-8")
    ks = _keystream(password, len(payload))
    cipher = bytes(a ^ b for a, b in zip(payload, ks))
    return base64.b64encode(cipher)


def decrypt_records(blob_b64, password):
    cipher = base64.b64decode(blob_b64)
    ks = _keystream(password, len(cipher))
    payload = bytes(a ^ b for a, b in zip(cipher, ks))
    return json.loads(payload.decode("utf-8"))


# ---- 5. csv/kml export ----


def to_csv_string(records):
    if not records:
        return ""
    fieldnames = list(records[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in records:
        writer.writerow(r)
    return buf.getvalue()


def to_kml_string(records, name="Ctrl + Fly Flight Track"):
    coord_lines = []
    for r in records:
        try:
            coord_lines.append(f"{float(r['lon'])},{float(r['lat'])},{float(r.get('alt_m') or 0)}")
        except (TypeError, ValueError, KeyError):
            continue
    coords = "\n          ".join(coord_lines)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <Placemark>
      <name>{name}</name>
      <LineString>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>
          {coords}
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""
