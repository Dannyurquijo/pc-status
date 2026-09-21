"""
Restart Program Utility for Windows
Restarts any specified application by process name or PID, fetching its original executable path.
"""
import sys
import os
import time
import subprocess
import psutil

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_running_apps():
    """Get list of active processes with unique names and executable paths."""
    apps = {}
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            name = proc.info['name']
            exe = proc.info['exe']
            if name and exe and os.path.exists(exe):
                if name.lower() not in apps:
                    apps[name.lower()] = {
                        "name": name,
                        "pids": [proc.info['pid']],
                        "exe": exe
                    }
                else:
                    apps[name.lower()]["pids"].append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return apps

def restart_program(target_name_or_pid):
    """Find process, terminate all instances, and relaunch from original exe path."""
    print(f"\n[INFO] Buscando programa: '{target_name_or_pid}'...")
    
    exe_to_launch = None
    target_pids = []
    app_name = target_name_or_pid

    # Check if target is numeric PID
    if str(target_name_or_pid).isdigit():
        pid = int(target_name_or_pid)
        try:
            proc = psutil.Process(pid)
            app_name = proc.name()
            exe_to_launch = proc.exe()
            target_pids.append(pid)
        except Exception as e:
            print(f"[ERROR] No se encontro el PID {pid}: {e}")
            return False
    else:
        search = str(target_name_or_pid).lower().strip()
        search_exe = search if search.endswith('.exe') else search + '.exe'

        apps = get_running_apps()
        matched = None
        for key, info in apps.items():
            if key == search or key == search_exe or search in key:
                matched = info
                break

        if not matched:
            print(f"[ERROR] No se encontro ningun programa en ejecucion que coincida con '{target_name_or_pid}'.")
            return False

        app_name = matched['name']
        exe_to_launch = matched['exe']
        target_pids = matched['pids']

    print(f"[OK] Programa encontrado: {app_name}")
    print(f"[OK] Ruta del ejecutable: {exe_to_launch}")
    print(f"[INFO] Cerrando {len(target_pids)} instancia(s) del programa...")

    for pid in target_pids:
        try:
            p = psutil.Process(pid)
            p.terminate()
        except Exception:
            pass

    gone, alive = psutil.wait_procs([psutil.Process(p) for p in target_pids if psutil.pid_exists(p)], timeout=3)
    for p in alive:
        try:
            p.kill()
        except Exception:
            pass

    print("[INFO] Esperando 2 segundos para asegurar cierre limpio...")
    time.sleep(2)

    print(f"[INFO] Reabriendo {app_name}...")
    try:
        subprocess.Popen([exe_to_launch], cwd=os.path.dirname(exe_to_launch), shell=True)
        print(f"[EXITO] {app_name} ha sido reiniciado con exito!")
        return True
    except Exception as e:
        print(f"[ERROR] Error al reiniciar {app_name}: {e}")
        return False

def interactive_menu():
    print("==================================================")
    print("       REINICIADOR DE PROGRAMAS - WINDOWS         ")
    print("==================================================")
    
    apps = get_running_apps()
    sorted_apps = sorted(apps.values(), key=lambda a: a['name'].lower())

    print("\nProgramas principales en ejecucion:")
    display_limit = min(15, len(sorted_apps))
    for i in range(display_limit):
        app = sorted_apps[i]
        print(f"  [{i+1}] {app['name']} (PIDs: {', '.join(map(str, app['pids']))})")
    
    print("\n--------------------------------------------------")
    choice = input("Escribe el NUMERO del programa o el NOMBRE (ejemplo: chrome, discord, obsidian): ").strip()
    
    if not choice:
        print("Operacion cancelada.")
        return

    if choice.isdigit() and 1 <= int(choice) <= display_limit:
        target_app = sorted_apps[int(choice) - 1]
        restart_program(target_app['name'])
    else:
        restart_program(choice)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        restart_program(sys.argv[1])
    else:
        interactive_menu()
