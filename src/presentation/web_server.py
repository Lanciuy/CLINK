from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import HttpUrl
import os

from domain.models import BatchDownloadRequest
from use_cases.local_storage import LocalStorage
from use_cases.batch_processor import BatchProcessor
from infrastructure.os_system_adapter import OSSystemAdapter
from presentation.websocket_manager import WebSocketManager
import asyncio

app = FastAPI(title="Local Media Downloader Engine")

# Setup dependencies
storage = LocalStorage(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "downloads"))
processor = BatchProcessor(storage)
ws_manager = WebSocketManager()
os_adapter = OSSystemAdapter()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.post("/api/download")
async def start_downloads(request: BatchDownloadRequest):
    """Starts a batch download job."""
    
    # Define a callback to push to websockets
    def progress_callback(data):
        # We need to run the async broadcast in the background
        # since the callback might be called from a different thread
        try:
             loop = asyncio.get_running_loop()
             loop.create_task(ws_manager.broadcast_progress(data))
        except RuntimeError:
             pass
        
    urls = [str(url) for url in request.urls]
    
    # Run the processor in the background
    asyncio.create_task(processor.process_batch(urls, progress_callback))
    
    return {"message": "Downloads started", "count": len(urls)}

@app.post("/api/open-folder")
async def open_folder():
    """Opens the download folder natively."""
    os_adapter.open_folder(storage.get_download_path())
    return {"message": "Folder opened"}

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the client, just keep the connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
