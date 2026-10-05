import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import runpy

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    print(f"[Render Fix] Dummy server listening on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()

    print("[Render Fix] Launching py.py in the same process...")
    try:
        runpy.run_path("py.py", run_name="__main__")
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot startup failed: {e}")
        raise
