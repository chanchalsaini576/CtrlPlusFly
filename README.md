# Ctrl + Fly

Drone flight simulator + telemetry analysis project. Frontend part me ek simulator hai
(4 zones, 3 levels, camera switching waghera) aur ek research page jisme drone history aur
Q6 / Asteria ke baare me likha hai. Backend Python (Flask) me hai jo flight data
generate/validate/encrypt karta hai aur usse CSV + KML files me export karta hai.

Made by Chanchal Saini.

## Requirements

- Python 3.9 ya usse upar (`python --version` se check kar lo)
- VS Code (ya koi bhi editor, VS Code ke liye niche steps diye hai)

## Folder structure

- `index.html`, `simulator.html`, `research.html`, `telemetry.html`, `about.html` — saare pages
- `zones/` — simulator ke 4 zones (desert, city, arctic, ocean)
- `css/style.css` — poore site ka styling
- `js/` — `hud.js` (corner telemetry widget), `zone-sim.js` (simulator logic), `telemetry-console.js` (backend se baat karne wala JS)
- `backend/` — Flask server + telemetry logic + testing ke liye ek sample CSV

## Kaise chalayein (VS Code)

1. Zip extract karo, VS Code me folder open karo (`File → Open Folder`).
2. Terminal khol lo (`` Ctrl+` ``).
3. Virtual environment bana lo (optional hai, lekin better rehta hai):
   ```bash
   python -m venv venv
   ```
   Activate karne ke liye:
   ```bash
   venv\Scripts\activate       # windows
   source venv/bin/activate    # mac / linux
   ```
4. Dependencies install karo:
   ```bash
   pip install -r backend/requirements.txt
   ```
5. Server run karo:
   ```bash
   python backend/app.py
   ```
6. Browser me kholo → **http://127.0.0.1:5000**

Server band karne ke liye terminal me `Ctrl+C` daba do.

**Port 5000 already use ho raha ho to** (macOS pe aksar AirPlay ki wajah se ho jata hai):
`backend/app.py` ki sabse aakhri line me `port=5000` ko `port=5050` kar do, aur
browser me `http://127.0.0.1:5050` kholo.

## Backend kya kya karta hai

Flask server do kaam karta hai — pehla, poori website serve karta hai (saari html/css/js
files), aur dusra, kuch API routes deta hai jo Telemetry page ka live console use karta hai:

| Route | Kaam |
|---|---|
| `/api/telemetry/generate` | ek sample flight bana deta hai (zone/level/duration lekar) |
| `/api/telemetry/upload-csv` | apni khud ki CSV upload karke validate karwa sakte ho |
| `/api/telemetry/encrypt` | current flight ko password se encrypt kar deta hai |
| `/api/telemetry/validate` | encrypted file ko decrypt + validate karta hai |
| `/api/telemetry/csv` | final flight ko CSV file me download karta hai |
| `/api/telemetry/kml` | final flight ko KML file me download karta hai (Google Earth me khulti hai) |

**Try karne ka sabse aasan tareeka**: Telemetry page kholo → "Generate Sample Flight" dabao →
records aa jayenge → "Download CSV" / "Download KML" se save kar lo.

Do sample files bhi diye hai `backend/sample_data/` me testing ke liye:

- `sample_flight_log.csv` — ek poori 10-minute flight ka plain CSV log (151 records).
  Ise "…upload your own flight-log CSV" section me daal ke validate karwa sakte ho.
- `sample_flight_encrypted.enc` — wahi flight, already encrypted (password: `ctrlfly-demo`).
  Ise "Upload an .enc file" section me daal ke, password `ctrlfly-demo` bhar ke seedha
  decrypt + validate flow test kar sakte ho — bina pehle encrypt kiye.

**Encryption ke baare me**: ye ek simple password-based XOR cipher hai, sirf ye dikhane
ke liye ki encrypted flight record ko decrypt + validate kaise karte hai. Real project
me security ke liye iska use mat karna — uske liye Python ki `cryptography` library

(Fernet) use karna better rahega.

## Sirf frontend dekhna ho (bina backend chalaye)

Agar sirf simulator ya research pages dekhne hai, to seedha `index.html` ko double-click
karke browser me khol lo — sab kaam karega. Sirf Telemetry page ka "Analysis Console"
wala live part backend maangega, kyunki wo real Python se baat karta hai.

---
Chanchal Saini
