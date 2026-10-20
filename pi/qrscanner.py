import cv2
import numpy as np
import time
import json
import os
import sys
import threading
import requests
import urllib3
from datetime import datetime
from flask import Flask, Response
"""
from contextlib import contextmanager # zum unterdrücken von Corrupt JPEG Warnungen

# Ungesicherte HTTPS-Warnungen (wegen IP-Aufruf) stummschalten
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
cv2.setLogLevel(0)  # OpenCV-Log-Level auf Fehler reduzieren

@contextmanager
def suppress_stderr():
    stderr_backup = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)

    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(stderr_backup, 2)
        os.close(stderr_backup)
        os.close(devnull)
"""

# --- KONFIGURATION & PI-AUSWAHL ---
API_BASE_URL = "https://demo.dpp.tmdt.uni-wuppertal.de/api/trigger"
LOG_DATEI = "scan_log.json"
SPERR_DAUER = 30  # Sekunden

# Liest Pi-Nummer aus dem Startbefehl (z.B. python3 qr_scanner.py 2), sonst Standard = 1
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
    led_erfolg, led_sperre = LED(5), LED(13)
    GPIO_ACTIVE = True
    for led in (led_erfolg, led_sperre): led.on()
    time.sleep(0.5)
    for led in (led_erfolg, led_sperre): led.off()
    print(f"🟢 LEDs aktiv | Konfiguriert als Raspberry Pi #{STEP_NUMBER}")
except ImportError:
    GPIO_ACTIVE = False
    print("⚠️ 'gpiozero' nicht gefunden – läuft ohne LEDs.")

# ---------------------------- Globale Variablen ----------------------------------
app = Flask(__name__)
qr_scanner = None
# ---------------------------------------------------------------------------------

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

class CamThread(threading.Thread):
    def __init__(self, camera_id):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.cap = None
        self.frame = None
        self.lock = threading.Lock() # Schutz für self.frame
        self.running = True
        self.start()

    def connect_camera(self):
        print(f"Verbinde mit Kamera {self.camera_id}")
        try:
            cap = cv2.VideoCapture(self.camera_id)
            if not cap.isOpened():
                print(f"Kamera {self.camera_id} nicht gefunden")
                cap.release()
                return False
            cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap = cap
            print(f"Kamera {self.camera_id} verbunden")
            return True

        except Exception as e:
            print(f"Fehler beim Verbinden mit Kamera: {e}")
            self.cap = None
            return False
    
    def disconnect_camera(self):
        cap = self.cap
        if self.cap is not None:
            print(f"Kamera {self.camera_id}: schließe Verbindung")
            try:
                self.cap.release()
            except Exception as e:
                print(f"Fehler beim Schließen der Kamera {self.camera_id}: {e}")
                pass
            self.cap = None
            with self.lock:
                self.frame = None
    
    def run(self):
        while self.running:
            # Kamera Initialisieren
            if self.cap is None:
                if not self.connect_camera(): # wiederholen bei Fehlschlag
                    time.sleep(2)
                    continue
            # Frame lesen
            #with suppress_stderr():  # Unterdrückt Corrupt JPEG Warnungen
            try:
                ret, frame = self.cap.read()
            except cv2.error as e:
                print(f"OpenCV-Kamerafehler: {e}")
                
                self.disconnect_camera()
                time.sleep(2)
                continue
            
            except Exception as e:
                print(f"Unerwarteter Kamerafehler: {e}")
                self.disconnect_camera()
                time.sleep(2)
                continue
            
            if not ret:
                print(f"Kamera {self.camera_id} Frame konnte nicht gelesen werden")
                self.disconnect_camera()
                time.sleep(2)
                continue
            
            # aktuellen Frame speichern
            with self.lock:
                self.frame = frame.copy()
            
    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

class QRScannerThread(threading.Thread):
    def __init__(self, camera):
        super().__init__(daemon=True)

        self.camera = camera
        # Sekunden zwischen Scans
        self.scan_interval = 0.2 # 0.2 = 5 Scans pro Sekunde 
        self.qr_detector = cv2.QRCodeDetector()
        self.overlay_lock = threading.Lock()
        self.qr_points = None
        self.qr_scan_time = 0
        # Wie lange der Rahmen sichtbar bleiben soll
        self.qr_overlay_duration = 0.1
        self.gescannte_codes = {}
        self.codes_lock = threading.Lock()
        self.start()

    def get_qr_overlay(self):
        # Übergibt Position des letzten gescannten QR-Codes und Zeitpunkt des Scans für grünen Rahmen
        with self.overlay_lock:
            if self.qr_points is None:
                return None, 0
            return self.qr_points.copy(), self.qr_scan_time

    def get_scan_count(self):
        #Liefert die Anzahl momentan gesperrter QR-Codes.
        with self.codes_lock:
            return len(self.gescannte_codes)

    def run(self):
        print("QR-Scanner-Thread gestartet.")
        while True:
            start_time = time.time()
            try:
                # Sperrmechanismus Teil 1: Abgelaufene Sperren entfernen
                jetzt = time.time()
                with self.codes_lock:
                    # Abgelaufene Sperren entfernen
                    abgelaufene_codes = [
                        code
                        for code, timestamp
                        in self.gescannte_codes.items()
                        if jetzt - timestamp >= SPERR_DAUER
                    ]
                    for code in abgelaufene_codes:
                        del self.gescannte_codes[code]
                
                # Aktuelles Kamerabild holen
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(self.scan_interval)
                    continue
                # QR-Code suchen
                data, points, _ = self.qr_detector.detectAndDecode(frame)
                if data and points is not None:
                    with self.overlay_lock:
                        self.qr_points = points.copy()
                        self.qr_scan_time = time.time()

                qr_daten = data.strip()
                
                if not qr_daten:
                    continue
                
                # Sperrmechanismus Teil 2
                with self.codes_lock:
                    # Prüfen, ob dieser Code noch gesperrt ist
                    if qr_daten in self.gescannte_codes:
                        bereits_gescannt = True
                    else:
                        bereits_gescannt = False
                        self.gescannte_codes[qr_daten] = jetzt
                        
                # Neuer QR-Code
                if not bereits_gescannt:
                    print(f"\nQR-Code erkannt: {qr_daten}")
                    pulse_led(led_erfolg, 0.5)

                    # API-Aufruf im Hintergrund
                    threading.Thread(target=send_sscc_trigger,args=(qr_daten,),daemon=True).start()
                
                    # Logging im Hintergrund
                    threading.Thread(target=logge_scan,args=(qr_daten,),daemon=True).start()

                # QR-Code noch gesperrt
                else:
                    print(".", end="", flush=True)
                    # Rotes LED-Feedback
                    pulse_led(led_sperre, 0.2)

            except cv2.error as e:
                print(f"\nOpenCV-Fehler im QR-Scanner-Thread: {e}")

            except Exception as e:
                print(f"\nFehler im QR-Scanner-Thread: {e}")

            # Scan-Intervall einhalten
            elapsed = time.time() - start_time
            sleep_time = self.scan_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

def generate_frames():
    STREAM_FPS = 15
    FRAME_INTERVAL = 1.0 / STREAM_FPS
    letzter_frame = 0

    while True:
        jetzt = time.time()
        # Stream auf 15 FPS begrenzen
        if jetzt - letzter_frame < FRAME_INTERVAL:
            time.sleep(0.001)
            continue
        # Aktuelles Kamerabild holen
        frame = cam1.get_frame()
        if frame is None:
            time.sleep(0.01)
            continue

        letzter_frame = jetzt
        
        # Informationen über letzten QR-Scan holen
        qr_points, qr_scan_time = qr_scanner.get_qr_overlay()
        # Grünen Rahmen nur kurz nach einem Scan anzeigen
        if (qr_points is not None and time.time() - qr_scan_time < qr_scanner.qr_overlay_duration):
            pts = qr_points.reshape(-1, 2).astype(int)
            for i in range(4):
                p1 = tuple(pts[i])
                p2 = tuple(pts[(i + 1) % 4])
                cv2.line(frame,p1,p2,(0, 255, 0),3)
        # Text anzeigen
        scan_count = qr_scanner.get_scan_count()
        cv2.putText(frame,f"Pi #{STEP_NUMBER} | Sperren: {scan_count}",(10, 30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0, 255, 0),2)
        # JPEG erzeugen
        ret, buffer = cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,70])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        # MJPEG Frame an Flask senden
        yield (b"--frame\r\n"b"Content-Type: image/jpeg\r\n\r\n"+ frame_bytes+ b"\r\n")

# --- WEBOBERFLÄCHE (CONSTRUCT-X DASHBOARD) ---
@app.route('/')
def index():
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Construct-X - Pi #{STEP_NUMBER}</title>
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
        .logo {{
            height: 38px;
            width: auto;
            object-fit: contain;
        }}
        .brand-text {{
            display: flex;
            flex-direction: column;
        }}
        .project-name {{
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #94a3b8;
        }}
        .title {{ 
            font-size: 1.15rem; 
            font-weight: 600; 
            color: #38bdf8; 
        }}
        .badge {{
            background: #E94509; /* Projekt Orange */
            color: white;
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .step-info {{
            font-size: 1rem;
            color: #94a3b8;
            margin-bottom: 1.25rem;
        }}
        .video-box {{
            position: relative;
            border-radius: 8px;
            border: 2px solid #3b82f6;
            background: #000;
            display: inline-block;
            overflow: hidden;
            width: 100%;
            max-width: 640px;
        }}
        .video-box img {{
            display: block;
            width: 100%;
            height: auto;
        }}
        .status-bar {{
            margin-top: 1.25rem;
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            font-size: 0.85rem;
            color: #cbd5e1;
        }}
        .status-item {{ display: flex; align-items: center; gap: 0.4rem; }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
        .dot-green {{ background: #22c55e; box-shadow: 0 0 8px #22c55e; }}
        .dot-red {{ background: #ef4444; box-shadow: 0 0 8px #ef4444; }}
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
    cam1 = CamThread(0)  # Kamera-Thread starten
    qr_scanner = QRScannerThread(cam1)  # QR-Scanner-Thread starten
    print(f"🚀 Starte Scanner für Raspberry Pi #{STEP_NUMBER} ({STEP_BEZEICHNUNG})")
    app.run(host='0.0.0.0', port=5000, threaded=True)