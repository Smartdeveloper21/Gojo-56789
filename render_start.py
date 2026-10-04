import os
import threading
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer

def run_dummy_server():
    # Grabs the dynamic port from Render (defaults to 10000)
    port = int(os.environ.get("PORT", 10000)) 
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"[Render Fix] Dummy server listening on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    # 1. Start the port server in the background so Render stays happy
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # 2. Launch your original bot file (py.py) automatically
    print("[Render Fix] Launching your bot script (py.py)...")
    subprocess.run(["python", "py.py"])
