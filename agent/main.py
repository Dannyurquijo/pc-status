"""
PC Status Main Daemon Agent
Ultra-lightweight HTTP API & Static Web Server in pure Python.
Secured with mandatory PIN authentication for all endpoints,
3-strike intrusion lockout, email alerts, and local batch unlocker.
"""
import os
import sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import json
import time
import smtplib
import datetime
import functools
import traceback
import subprocess
import threading
import http.server
import socketserver
import urllib.parse
import psutil
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
import hardware

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SECURITY_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "security_alert.log")

# Global Security State
FAILED_ATTEMPTS = 0
IS_LOCKED = False
LOCK_REASON = ""

def load_config():
    default_config = {
        "security_pin": "1532",
        "server_port": 5000,
        "poll_interval_seconds": 2.5,
        "max_failed_attempts": 3,
        "alert_email": "durquijob@gmail.com",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": ""
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_config.update(cfg)
        except Exception as e:
            print(f"Error al cargar config.json: {e}", flush=True)
    return default_config

CONFIG = load_config()

def send_security_alert(client_ip):
    """Log security incident and attempt sending email alert."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recipient = CONFIG.get("alert_email", "durquijob@gmail.com")
    
    log_msg = f"[{timestamp}] ALERTA DE SEGURIDAD: 3 intentos fallidos de PIN desde IP {client_ip}. SISTEMA BLOQUEADO.\n"
    print(log_msg, flush=True)
    
    try:
        with open(SECURITY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_msg)
    except Exception:
        pass

    # Try sending SMTP email if configured
    smtp_user = CONFIG.get("smtp_user")
    smtp_pass = CONFIG.get("smtp_password")
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient
            msg['Subject'] = "🚨 ALERTA DE SEGURIDAD: Bloqueo de PC Status en tu Laptop"
            
            body = f"""
Hola,

Se ha activado el BLOQUEO DE SEGURIDAD en tu aplicación PC Status.

Detalles del Incidente:
- Fecha y Hora: {timestamp}
- Origen de la Solicitud: IP {client_ip}
- Motivo: 3 intentos fallidos de PIN de seguridad.

El sistema ha rechazado todas las conexiones y permanecerá totalmente BLOQUEADO hasta que ejecutes el archivo 'unlock_agent.bat' directamente en tu laptop.

Atentamente,
Sistema de Seguridad PC Status
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(CONFIG.get("smtp_server", "smtp.gmail.com"), int(CONFIG.get("smtp_port", 587)))
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            print(f"[OK] Correo de alerta enviado exitosamente a {recipient}", flush=True)
        except Exception as e:
            print(f"[AVISO] Alerta registrada localmente. Error enviando correo SMTP: {e}", flush=True)

class PCStatusHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        try:
            self.send_response(200, "ok")
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type, Authorization, X-Security-PIN")
            self.end_headers()
        except Exception as e:
            print(f"Error en OPTIONS: {e}", flush=True)

    def _send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_post_data(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                raw_data = self.rfile.read(content_length).decode('utf-8')
                return json.loads(raw_data)
        except Exception:
            pass
        return {}

    def _get_client_ip(self):
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0]

    def _validate_pin_request(self, payload=None):
        global FAILED_ATTEMPTS, IS_LOCKED, LOCK_REASON

        if IS_LOCKED:
            return False, f"🚨 SISTEMA BLOQUEADO POR SEGURIDAD (3 intentos fallidos registrados). Alerta enviada a {CONFIG.get('alert_email')}. Para desbloquear, ejecuta 'unlock_agent.bat' en tu laptop."

        # Extract PIN from Header 'X-Security-PIN', query string, or JSON payload
        pin_sent = self.headers.get("X-Security-PIN", "").strip()
        
        if not pin_sent and payload and isinstance(payload, dict):
            pin_sent = str(payload.get("pin", "")).strip()

        if not pin_sent:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if "pin" in params:
                pin_sent = params["pin"][0].strip()

        expected_pin = str(CONFIG.get("security_pin", "1532")).strip()

        if pin_sent == expected_pin:
            FAILED_ATTEMPTS = 0
            return True, "Autenticado"

        # Increment failed attempt
        FAILED_ATTEMPTS += 1
        client_ip = self._get_client_ip()
        print(f"[SEGURIDAD] Intento fallido de PIN (#{FAILED_ATTEMPTS}) desde IP {client_ip}", flush=True)

        if FAILED_ATTEMPTS >= int(CONFIG.get("max_failed_attempts", 3)):
            IS_LOCKED = True
            LOCK_REASON = f"3 intentos fallidos desde {client_ip}"
            send_security_alert(client_ip)
            return False, f"🚨 SISTEMA BLOQUEADO POR SEGURIDAD (3 intentos fallidos). Se ha notificado a {CONFIG.get('alert_email')}. Desbloquea ejecutando 'unlock_agent.bat' en tu computadora."

        remaining = int(CONFIG.get("max_failed_attempts", 3)) - FAILED_ATTEMPTS
        return False, f"PIN incorrecto. Quedan {remaining} intento(s) antes del bloqueo permanente."

    def do_GET(self):
        try:
            url_path = urllib.parse.urlparse(self.path).path
            
            # Unrestricted static asset requests (UI html/css/js)
            if url_path in ['/', '/index.html', '/style.css', '/app.js', '/manifest.json', '/favicon.ico']:
                return super().do_GET()

            # API Unlocking Route (Only allowed via local call or explicit reset)
            if url_path == '/api/unlock':
                global IS_LOCKED, FAILED_ATTEMPTS
                client_ip = self._get_client_ip()
                if client_ip in ['127.0.0.1', 'localhost', '::1']:
                    IS_LOCKED = False
                    FAILED_ATTEMPTS = 0
                    self._send_json({"success": True, "message": "Sistema desbloqueado exitosamente."})
                else:
                    self._send_json({"success": False, "error": "El desbloqueo solo se puede ejecutar desde la laptop local."}, status_code=403)
                return

            # Protected API Routes (GET /api/status, GET /api/processes)
            if url_path.startswith('/api/'):
                valid, msg = self._validate_pin_request()
                if not valid:
                    status = 403 if IS_LOCKED else 401
                    self._send_json({"success": False, "error": msg, "locked": IS_LOCKED}, status_code=status)
                    return

                if url_path == '/api/status':
                    telemetry = hardware.get_full_telemetry()
                    self._send_json({"success": True, "data": telemetry})
                    return

                elif url_path == '/api/processes':
                    procs = hardware.get_top_processes(limit=20)
                    self._send_json({"success": True, "processes": procs})
                    return

            return super().do_GET()
        except Exception as e:
            print(f"Error procesando GET {self.path}: {e}", flush=True)
            traceback.print_exc()
            try:
                self._send_json({"success": False, "error": str(e)}, status_code=500)
            except Exception:
                pass

    def do_POST(self):
        try:
            url_path = urllib.parse.urlparse(self.path).path
            payload = self._get_post_data()

            valid, msg = self._validate_pin_request(payload)
            if not valid:
                status = 403 if IS_LOCKED else 401
                self._send_json({"success": False, "error": msg, "locked": IS_LOCKED}, status_code=status)
                return

            if url_path == '/api/kill-process':
                pid = payload.get("pid")
                if not pid:
                    self._send_json({"success": False, "error": "PID no especificado"}, status_code=400)
                    return
                try:
                    proc = psutil.Process(int(pid))
                    proc_name = proc.name()
                    proc.terminate()
                    self._send_json({"success": True, "message": f"Proceso {proc_name} (PID {pid}) cerrado correctamente."})
                except psutil.NoSuchProcess:
                    self._send_json({"success": True, "message": "El proceso ya no estaba en ejecución."})
                except Exception as e:
                    self._send_json({"success": False, "error": f"Error al cerrar proceso: {str(e)}"}, status_code=500)
                return

            elif url_path == '/api/restart-process':
                pid = payload.get("pid")
                name = payload.get("name")
                if not pid and not name:
                    self._send_json({"success": False, "error": "PID o nombre no especificado"}, status_code=400)
                    return
                try:
                    import restart_program
                    target = pid if pid else name
                    success = restart_program.restart_program(target)
                    if success:
                        self._send_json({"success": True, "message": f"Programa {name or pid} reiniciado correctamente."})
                    else:
                        self._send_json({"success": False, "error": f"No se pudo reiniciar el programa {name or pid}."})
                except Exception as e:
                    self._send_json({"success": False, "error": f"Error al reiniciar programa: {str(e)}"}, status_code=500)
                return

            elif url_path == '/api/shutdown':
                self._send_json({"success": True, "message": "Iniciando apagado de emergencia de la PC en 30 segundos..."})
                def _shutdown():
                    time.sleep(2)
                    if sys.platform == 'win32':
                        os.system("shutdown /s /f /t 30 /c \"Apagado remoto de emergencia desde PC Status\"")
                    else:
                        os.system("shutdown -h now")
                threading.Thread(target=_shutdown, daemon=True).start()
                return

            elif url_path == '/api/stop-agent':
                self._send_json({"success": True, "message": "Desactivando agente de monitoreo de PC..."})
                def _stop():
                    time.sleep(1)
                    os._exit(0)
                threading.Thread(target=_stop, daemon=True).start()
                return

            self._send_json({"success": False, "error": "Ruta POST no encontrada"}, status_code=404)
        except Exception as e:
            print(f"Error procesando POST {self.path}: {e}", flush=True)
            traceback.print_exc()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run_server():
    port = int(CONFIG.get("server_port", 5000))
    handler = functools.partial(PCStatusHandler, directory=WEB_DIR)
    server = ThreadedHTTPServer(('0.0.0.0', port), handler)
    print(f"==================================================", flush=True)
    print(f" PC Status Agent SEGURIDAD REFORZADA ", flush=True)
    print(f" Puerto local: http://localhost:{port}", flush=True)
    print(f" PIN de seguridad: {CONFIG.get('security_pin')}", flush=True)
    print(f" Máximo de intentos: {CONFIG.get('max_failed_attempts')} (Notificación a {CONFIG.get('alert_email')})", flush=True)
    print(f"==================================================", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor de monitoreo...", flush=True)
        server.server_close()

if __name__ == '__main__':
    run_server()
