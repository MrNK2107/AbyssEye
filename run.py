#!/usr/bin/env python3
"""
==============================================================================
ABYSSEYE: Full-Stack Ground Station Launcher (SIH Problem 26057)
Auto-cleans occupied ports, starts Backend (8000) & Frontend (3000),
and cleanly handles Ctrl+C shutdown.
==============================================================================
"""

import os
import sys
import time
import signal
import socket
import shutil
import urllib.request
import webbrowser
import subprocess
from typing import List

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

def is_port_in_use(port: int) -> bool:
    """Checks if a local TCP port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((BACKEND_HOST, port)) == 0

def kill_process_on_port(port: int):
    """Gracefully terminates any process occupying the given port."""
    if not is_port_in_use(port):
        return

    try:
        if sys.platform == "win32":
            cmd = f'netstat -ano | findstr :{port}'
            try:
                output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
                pids = set()
                for line in output.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and f":{port}" in parts[1]:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) > 0 and int(pid) != os.getpid():
                            pids.add(pid)

                for pid in pids:
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:
            subprocess.run(f"fuser -k {port}/tcp", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(0.5)
    except Exception:
        pass

def wait_for_service(url: str, timeout_sec: int = 25) -> bool:
    """Polls a URL until it responds with HTTP 200 or timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AbyssEye-Launcher'})
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.getcode() in [200, 304]:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("=================================================================", flush=True)
    print("  ABYSSEYE — Autonomous Sonar Ground Station (SIH 26057)         ", flush=True)
    print("=================================================================", flush=True)

    # 1. Clean any occupied ports
    kill_process_on_port(BACKEND_PORT)
    kill_process_on_port(FRONTEND_PORT)

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    if not shutil.which(npm_cmd.replace(".cmd", "")) and not shutil.which(npm_cmd):
        print("[ERROR] 'npm' was not found in your system PATH.", flush=True)
        sys.exit(1)

    processes: List[subprocess.Popen] = []

    def cleanup(sig=None, frame=None):
        for p in processes:
            if p.poll() is None:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    p.terminate()
        kill_process_on_port(BACKEND_PORT)
        kill_process_on_port(FRONTEND_PORT)
        print("\n[✓] All services stopped. Goodbye!\n", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # 2. Launch FastAPI Backend
        backend_cmd = [
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)
        ]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=os.getcwd(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        processes.append(backend_proc)

        # 3. Launch Next.js Frontend
        frontend_cmd = [npm_cmd, "run", "dev"]
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=os.path.join(os.getcwd(), "frontend"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        processes.append(frontend_proc)

        # 4. Wait for services to be ready
        backend_ready = wait_for_service(f"http://{BACKEND_HOST}:{BACKEND_PORT}/health", timeout_sec=15)
        frontend_ready = wait_for_service(f"http://localhost:{FRONTEND_PORT}", timeout_sec=25)

        if backend_ready and frontend_ready:
            print(f"[✓] FastAPI Backend running on http://{BACKEND_HOST}:{BACKEND_PORT}", flush=True)
            print(f"[✓] Next.js Frontend running on http://localhost:{FRONTEND_PORT}", flush=True)
            print(f"[✓] REST API Docs: http://{BACKEND_HOST}:{BACKEND_PORT}/docs", flush=True)
            print("-----------------------------------------------------------------", flush=True)
            print("[✓] Ground Station is LIVE. Opening browser... (Press Ctrl+C to stop)", flush=True)
            print("=================================================================\n", flush=True)

            try:
                webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
            except Exception:
                pass
        else:
            if not backend_ready:
                err = backend_proc.stderr.read().decode('utf-8', errors='ignore') if backend_proc.stderr else ""
                print(f"[ERROR] FastAPI Backend failed to start:\n{err}", flush=True)
            if not frontend_ready:
                err = frontend_proc.stderr.read().decode('utf-8', errors='ignore') if frontend_proc.stderr else ""
                print(f"[ERROR] Next.js Frontend failed to start:\n{err}", flush=True)
            cleanup()

        # Keep running until user presses Ctrl+C
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    cleanup()

    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        cleanup()

if __name__ == "__main__":
    main()
