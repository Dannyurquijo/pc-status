"""
PC Status Main Daemon Agent
Ultra-lightweight HTTP API & Static Web Server in pure Python.
Requires < 15MB RAM and < 0.5% CPU.
"""
import os
import sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import json
import time
import functools
import traceback
import subprocess
import threading
import http.server
import socketserver
import urllib.parse
import psutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hardware

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def load_config():
    default_config = {
        "security_pin": "1234",
        "server_port": 5000,
        "poll_interval_seconds": 2.5
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

class PCStatusHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        try:
            self.send_response(200, "ok")
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type, Authorization")
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

    def _validate_pin(self, payload):
        pin_sent = str(payload.get("pin", "")).strip()
        expected_pin = str(CONFIG.get("security_pin", "1234")).strip()
        return pin_sent == expected_pin

    def do_GET(self):
        try:
            url_path = urllib.parse.urlparse(self.path).path
            
            # API Routes
            if url_path == '/api/status':
                telemetry = hardware.get_full_telemetry()
                self._send_json({"success": True, "data": telemetry})
                return
                
            elif url_path == '/api/processes':
                procs = hardware.get_top_processes(limit=20)
                self._send_json({"success": True, "processes": procs})
                return

            # Serve static Web UI files
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

            if not self._validate_pin(payload):
                self._send_json({"success": False, "error": "PIN de seguridad incorrecto"}, status_code=401)
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
    print(f" PC Status Agent Iniciado Correctamente ", flush=True)
    print(f" Puerto local: http://localhost:{port}", flush=True)
    print(f" PIN de seguridad: {CONFIG.get('security_pin')}", flush=True)
    print(f" Servidor estático UI: Servido desde {WEB_DIR}", flush=True)
    print(f"==================================================", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor de monitoreo...", flush=True)
        server.server_close()

if __name__ == '__main__':
    run_server()
