from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import List
import os
import asyncio

from domain.models import DownloadRequest, BatchDownloadRequest, AnalyzeRequest, AnalyzeResponse, CookieSaveRequest, CookieSaveResponse
from use_cases.local_storage import LocalStorage
from use_cases.batch_processor import BatchProcessor
from use_cases.analyze_media import AnalyzeMediaUseCase
from use_cases.download_media import DownloadMediaUseCase
from infrastructure.ytdlp_engine import YTDLPEngine
from infrastructure.playwright_sniffer import PlaywrightSniffer
from infrastructure.ffmpeg_merger import FFmpegMerger
from infrastructure.local_cookie_manager import LocalCookieManager
from infrastructure.os_system_adapter import OSSystemAdapter
from presentation.websocket_manager import WebSocketManager

app = FastAPI(title="Clink Media Downloader")

# Setup dependencies
storage = LocalStorage(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "downloads"))
os_adapter = OSSystemAdapter()

from infrastructure.realesrgan_engine import RealESRGANEngine

# Infrastructure Adapters (Tier 1 to 4)
ytdlp_engine = YTDLPEngine(storage.get_download_path())
playwright_sniffer = PlaywrightSniffer()
cookie_manager = LocalCookieManager()
ffmpeg_merger = FFmpegMerger()
realesrgan_engine = RealESRGANEngine(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Use Cases
analyze_use_case = AnalyzeMediaUseCase(ytdlp_engine, playwright_sniffer, cookie_manager)
download_use_case = DownloadMediaUseCase(ytdlp_engine, playwright_sniffer, cookie_manager, ffmpeg_merger, realesrgan_engine)
processor = BatchProcessor(download_use_case, max_concurrent=5)
ws_manager = WebSocketManager()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

import traceback

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest):
    try:
        if not request.urls:
            raise Exception("No URLs provided")
        return await analyze_use_case.execute(request.urls[0], is_playlist=request.is_playlist)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

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
    asyncio.create_task(processor.process_batch(
        urls, 
        progress_callback, 
        enhance_images=request.enhance_images,
        format_type=request.format_type,
        is_playlist=request.is_playlist
    ))
    
    return {"message": "Downloads started", "count": len(urls)}

@app.post("/api/settings/cookies", response_model=CookieSaveResponse)
async def save_cookies(request: CookieSaveRequest):
    try:
        cookie_manager.save_cookies(request.cookie_content)
        return CookieSaveResponse(message="Cookies saved successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
