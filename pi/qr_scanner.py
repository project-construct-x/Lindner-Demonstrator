import cv2, numpy as np, time, json, os, sys, threading, requests, urllib3
from datetime import datetime
from flask import Flask, Response

# Ungesicherte HTTPS-Warnungen (wegen IP-Aufruf) stummschalten
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION & PI-AUSWAHL ---
API_BASE_URL = "https://132.195.160.160/api/trigger"
LOG_DATEI = "scan_log.json"
SPERR_DAUER = 30  # Sekunden

# Liest Pi-Nummer aus dem Startbefehl (z.B. python3 script.py 2), sonst Standard = 1
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
    # Kurzer Selbsttest beim Start
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
    """Schaltet eine LED für X Sekunden im Hintergrund an, ohne das Videobild zu blockieren."""
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

# Kamera & QR-Detector initialisieren
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
qr_detector = cv2.QRCodeDetector()

def generate_frames():
    global gescannte_codes
    frame_counter = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        aktuell = time.time()
        frame_counter += 1

        # Veraltete Sperren bereinigen
        gescannte_codes = {c: t for c, t in gescannte_codes.items() if aktuell - t < SPERR_DAUER}

        # QR-Erkennung in jedem 2. Frame
        if frame_counter % 2 == 0:
            data, points, _ = qr_detector.detectAndDecode(frame)
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
                    pts = points[0].astype(int)
                    for i in range(len(pts)):
                        cv2.line(frame, tuple(pts[i]), tuple(pts[(i + 1) % len(pts)]), (0, 255, 0), 3)

        cv2.putText(frame, f"Pi #{STEP_NUMBER} | Sperren: {len(gescannte_codes)}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.001)

@app.route('/')
def index():
    return f"""<html><head><title>Pi #{STEP_NUMBER}</title>
    <style>
    body {{ font-family: Arial, sans-serif; text-align: center; background: #111; color: white; }}
    img {{ border: 4px solid #00ff00; border-radius: 8px; margin-top: 20px; }}
    .badge {{ background: #0275d8; color: white; padding: 4px 8px; border-radius: 4px; }}
    </style></head>
    <body>
    <h1>📷 SSCC Scanner <span class="badge">Raspberry Pi #{STEP_NUMBER}</span></h1>
    <h3>Prozessschritt: {STEP_BEZEICHNUNG}</h3>
    <img src="/video_feed" width="640" height="480">
    </body></html>"""

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print(f"🚀 Starte Scanner für Raspberry Pi #{STEP_NUMBER} ({STEP_BEZEICHNUNG})")
    app.run(host='0.0.0.0', port=5000, threaded=True)