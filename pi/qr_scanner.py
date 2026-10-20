import cv2
import numpy as np
import time
import json
import os
import sys
import glob
import threading
import requests
import urllib3
from datetime import datetime
from flask import Flask, Response

# Ungesicherte HTTPS-Warnungen stummschalten
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION & PI-AUSWAHL ---
API_BASE_URL = "https://demo.dpp.tmdt.uni-wuppertal.de/api/trigger"
LOG_DATEI = "scan_log.json"
SPERR_DAUER = 30  # Sekunden

STEP_NUMBER = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
STEP_NAMES = {
    1: "Schritt 1: Ausgang beim Hersteller",
    2: "Schritt 2: Eingang / Transport Logistik",
    3: "Schritt 3: Wareneingang beim Empfänger"
}
STEP_BEZEICHNUNG = STEP_NAMES.get(STEP_NUMBER, f"Schritt {STEP_NUMBER}")

# --- GPIO LED SETUP ---
try:
    from gpiozero import LED
    led_erfolg, led_sperre = LED(4), LED(17)
    GPIO_ACTIVE = True
    for led in (led_erfolg, led_sperre): led.on()
    time.sleep(0.5)
    for led in (led_erfolg, led_sperre): led.off()
    print(f"🟢 LEDs aktiv | Konfiguriert als Raspberry Pi #{STEP_NUMBER}")
except ImportError:
    GPIO_ACTIVE = False
    print("⚠️ 'gpiozero' nicht gefunden – läuft ohne LEDs.")

app = Flask(__name__)
gescannte_codes = {}

def pulse_led(led, duration):
    if GPIO_ACTIVE:
        led.on()
        threading.Timer(duration, led.off).start()

def logge_scan(qr_daten):
    eintrag = {
        "pi_id": STEP_NUMBER,
        "schritt": STEP_BEZEICHNUNG,
        "datum_uhrzeit": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_epoch": time.time(),
        "sscc_qr_inhalt": qr_daten
    }
    logs = []
    if os.path.exists(LOG_DATEI):
        try:
            with open(LOG_DATEI, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            pass
    logs.append(eintrag)
    with open(LOG_DATEI, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    print(f"💾 Log gespeichert [Pi {STEP_NUMBER}]: {qr_daten}")

def send_sscc_trigger(sscc_code):
    try:
        res = requests.post(f"{API_BASE_URL}/{STEP_NUMBER}", json={"sscc": sscc_code}, timeout=4, verify=False)
        print(f"🚀 API-Trigger [{STEP_NUMBER}] Status: {res.status_code}")
    except Exception as e:
        print(f"❌ API-Fehler: {e}")

def get_placeholder_frame(text="Kamera getrennt..."):
    img = np.zeros((480, 640, 3), np.uint8)
    cv2.putText(img, text, (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
    _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
    return buffer.tobytes()

# --- OPTIMIERTER KAMERA-STREAM ---
class SafeCameraStream:
    def __init__(self):
        self.cap = cv2.VideoCapture()
        self.frame = None
        self.is_connected = False
        self.lock = threading.Lock()
        self.running = True
        self.placeholder = get_placeholder_frame(f"Pi #{STEP_NUMBER}: Warte auf Kamera...")
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _try_open_camera(self):
        # Schnelle Systemabfrage statt blinder Loop über Indizes
        devices = sorted(glob.glob('/dev/video*'))
        if not devices:
            return False

        for dev_path in devices:
            try:
                idx = int(dev_path.replace('/dev/video', ''))
                self.cap.open(idx, cv2.CAP_V4L2)
                if self.cap.isOpened():
                    # Puffergröße auf 1 setzen verhindert Frame-Stau und Latenz!
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    ret, test_frame = self.cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        print(f"🎥 Kamera erfolgreich auf {dev_path} verbunden.")
                        return True
                    self.cap.release()
            except Exception:
                if self.cap.isOpened():
                    self.cap.release()
        return False

    def _update_loop(self):
        while self.running:
            if not self.is_connected:
                if self._try_open_camera():
                    self.is_connected = True
                else:
                    time.sleep(3)  # Entlastet CPU bei fehlender Kamera
                    continue

            try:
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    with self.lock:
                        self.frame = frame
                else:
                    print("⚠️ Kameraverbindung verloren.")
                    self.is_connected = False
                    self.cap.release()
                    time.sleep(2)
            except Exception:
                self.is_connected = False
                self.cap.release()
                time.sleep(2)

            time.sleep(0.005)

    def read(self):
        with self.lock:
            if not self.is_connected or self.frame is None:
                return None
            return self.frame.copy()

cam_stream = SafeCameraStream()
qr_detector = cv2.QRCodeDetector()

def generate_frames():
    global gescannte_codes
    frame_counter = 0

    while True:
        frame = cam_stream.read()
        
        if frame is None:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + cam_stream.placeholder + b'\r\n')
            time.sleep(0.2)
            continue

        aktuell = time.time()
        frame_counter += 1
        gescannte_codes = {c: t for c, t in gescannte_codes.items() if aktuell - t < SPERR_DAUER}

        # QR-Erkennung alle 6 Frames
        if frame_counter % 6 == 0:
            small_frame = cv2.resize(frame, (320, 240))
            data, points, _ = qr_detector.detectAndDecode(small_frame)
            data = data.strip() if data else ""

            if data:
                if data not in gescannte_codes:
                    print(f"\n⚡ [Pi {STEP_NUMBER}] NEUER SSCC: {data}")
                    pulse_led(led_erfolg, 1.5)
                    threading.Thread(target=send_sscc_trigger, args=(data,), daemon=True).start()
                    gescannte_codes[data] = aktuell
                    logge_scan(data)
                else:
                    print(".", end="", flush=True)
                    pulse_led(led_sperre, 0.5)

                if points is not None:
                    pts = (points[0] * 2).astype(int)
                    for i in range(len(pts)):
                        cv2.line(frame, tuple(pts[i]), tuple(pts[(i + 1) % len(pts)]), (0, 255, 0), 3)

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.01)

# --- ROUTE: EINZEL-DASHBOARD (NUR LOKALER STREAM) ---
@app.route('/')
def index():
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Construct-X - Pi {STEP_NUMBER}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            background: #0f172a; 
            color: #f8fafc; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            min-height: 100vh; 
            padding: 2rem 1rem;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            max-width: 720px;
            width: 100%;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            text-align: center;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid #334155;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-align: left;
        }}
        .logo {{ height: 38px; width: auto; object-fit: contain; }}
        .brand-text {{ display: flex; flex-direction: column; }}
        .project-name {{
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #94a3b8;
        }}
        .title {{ font-size: 1.15rem; font-weight: 600; color: #38bdf8; }}
        .badge {{
            background: #E94509;
            color: white;
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .step-info {{ font-size: 1rem; color: #94a3b8; margin-bottom: 1.25rem; }}
        .video-box {{
            position: relative;
            border-radius: 8px;
            border: 2px solid #3b82f6;
            background: #000;
            display: block;
            overflow: hidden;
            width: 100%;
            max-width: 640px;
            margin: 0 auto;
            aspect-ratio: 4 / 3;
        }}
        .video-box img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="brand">
                <img src="/static/Logo_CX.png" alt="Construct-X Logo" class="logo" onerror="this.style.display='none'">
                <div class="brand-text">
                    <span class="project-name">Construct-X</span>
                    <span class="title">QR-Scanner</span>
                </div>
            </div>
            <span class="badge">Raspberry Pi #{STEP_NUMBER}</span>
        </div>
        <div class="step-info">
            Prozessschritt: <strong>{STEP_BEZEICHNUNG}</strong>
        </div>
        <div class="video-box">
            <img src="/video_feed" alt="Kamera Live-Stream">
        </div>
    </div>
</body>
</html>"""

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print(f"🚀 Starte Scanner für Raspberry Pi #{STEP_NUMBER} ({STEP_BEZEICHNUNG})")
    app.run(host='0.0.0.0', port=5000, threaded=True)