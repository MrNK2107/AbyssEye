#!/usr/bin/env python3
"""
==============================================================================
ABYSSEYE: Unified Full-Stack Ground Station Launcher (SIH Problem 26057)
Starts both FastAPI Backend (Port 8000) and Next.js Frontend (Port 3000).
Handles healthchecks, auto-browser launch, and clean multi-process termination.
==============================================================================
"""

import os
import sys
import time
import signal
import shutil
import urllib.request
import webbrowser
import subprocess
from typing import List, Optional

BACKEND_URL = "http://localhost:8000/health"
FRONTEND_URL = "http://localhost:3000"

def check_prerequisites():
    """Validates Python version, npm, and required folders."""
    if sys.version_info < (3, 9):
        print(f"[ERROR] Python 3.9+ is required. Detected: {sys.version}")
        sys.exit(1)

    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_path:
        print("[ERROR] 'npm' was not found in PATH. Please install Node.js (v18+).")
        sys.exit(1)

    if not os.path.exists("frontend"):
        print("[ERROR] 'frontend' directory not found in the project root.")
        sys.exit(1)

    if not os.path.exists(os.path.join("frontend", "node_modules")):
        print("[*] Installing frontend dependencies (npm install)...")
        subprocess.run([npm_path, "install"], cwd="frontend", check=True)

def wait_for_service(url: str, service_name: str, timeout_sec: int = 30) -> bool:
    """Polls a URL until it responds with HTTP 200 or timeout."""
    start_time = time.time()
    print(f"[*] Waiting for {service_name} at {url}...")
    while time.time() - start_time < timeout_sec:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AbyssEye-Launcher'})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.getcode() in [200, 304]:
                    print(f"[OK] {service_name} is UP and healthy!")
                    return True
        except Exception:
            time.sleep(0.8)
    print(f"[WARN] {service_name} health check timed out after {timeout_sec}s.")
    return False

def main():
    print("=================================================================")
    print("  ABYSSEYE — Full-Stack Sonar Ground Station Launcher           ")
    print("  SIH 2026 Problem 26057: Autonomous Underwater Debris System   ")
    print("=================================================================")

    check_prerequisites()

    processes: List[subprocess.Popen] = []
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Cleanup handler for graceful shutdown
    def shutdown(sig=None, frame=None):
        print("\n[*] Stopping AbyssEye backend and frontend services...")
        for p in processes:
            if p.poll() is None:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
                else:
                    p.terminate()
        print("[*] All services terminated cleanly. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        # 1. Start FastAPI Backend
        print("\n[1/2] Starting FastAPI Backend on http://localhost:8000...")
        backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=os.getcwd(),
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(backend_proc)

        # 2. Start Next.js Frontend
        print("[2/2] Starting Next.js Frontend on http://localhost:3000...")
        frontend_cmd = [npm_cmd, "run", "dev"]
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=os.path.join(os.getcwd(), "frontend"),
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(frontend_proc)

        # 3. Wait for Healthchecks
        backend_ok = wait_for_service(BACKEND_URL, "FastAPI Backend", timeout_sec=20)
        frontend_ok = wait_for_service(FRONTEND_URL, "Next.js Frontend", timeout_sec=30)

        if backend_ok and frontend_ok:
            print("\n=================================================================")
            print("  [SUCCESS] AbyssEye Ground Station is LIVE!                    ")
            print("  • Web Console: http://localhost:3000                           ")
            print("  • REST API:    http://localhost:8000/api/v1/sonar/health       ")
            print("  • API Docs:    http://localhost:8000/docs                      ")
            print("  Press Ctrl+C at any time to stop all services.                 ")
            print("=================================================================\n")

            # Open browser automatically
            try:
                webbrowser.open("http://localhost:3000")
            except Exception:
                pass

        # Keep parent alive while child processes are running
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"[WARN] Process {p.args} exited unexpectedly with code {p.returncode}.")
                    shutdown()

    except KeyboardInterrupt:
        shutdown()
    except Exception as e:
        print(f"[ERROR] Launcher failed: {e}")
        shutdown()

if __name__ == "__main__":
    main()
