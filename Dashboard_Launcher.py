"""
Admin Dashboard Direct Launcher
Starts the Node.js backend if available and opens the Admin Dashboard in your browser.
"""
import os
import sys
import webbrowser
import subprocess
import time
import urllib.request

def is_backend_running(port=4000):
    try:
        req = urllib.request.Request(f"http://localhost:{port}/api/health")
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            return resp.status == 200
    except Exception:
        return False

def main():
    # Get current directory of the exe/script
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    backend_dir = os.path.join(base_dir, "backend")
    server_js = os.path.join(backend_dir, "server.js")
    dashboard_html = os.path.join(base_dir, "admin_dashboard.html")

    # If backend exists and not running, start it quietly
    if os.path.exists(server_js) and not is_backend_running(4000):
        try:
            # 0x08000000 = CREATE_NO_WINDOW
            subprocess.Popen(["node", "server.js"], cwd=backend_dir, creationflags=0x08000000)
            time.sleep(1)
        except Exception:
            pass

    # Open dashboard html in default web browser
    if os.path.exists(dashboard_html):
        url = f"file:///{os.path.abspath(dashboard_html).replace(os.sep, '/')}"
        webbrowser.open(url)
    else:
        webbrowser.open("http://localhost:4000")

if __name__ == "__main__":
    main()

