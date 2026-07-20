import uvicorn
import webbrowser
import threading
import time
import os
import sys

# Ensure the 'src' directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from presentation.web_server import app

def launch_browser():
    """Automatically launches the user's default browser after a short delay."""
    time.sleep(1.5)  # Wait a bit for the server to start
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # Ensure downloads directory exists
    os.makedirs("downloads", exist_ok=True)
    
    # Start the browser launch thread
    threading.Thread(target=launch_browser, daemon=True).start()
    
    # Start the FastAPI web server
    uvicorn.run(app, host="127.0.0.1", port=8000)
