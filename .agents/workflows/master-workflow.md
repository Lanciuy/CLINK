---
description: Rule for Agent to build an unblockable Local Web Media Downloader (HD/4K) using Clean Architecture, 4-Tier Fallback Cascade Engine (yt-dlp + Playwright Stealth Interceptor), FFmpeg remuxing, and native OS Desktop integration at localhost:8000.
---

# AGENT WORKFLOW: LOCAL WEB ULTRA-HIGH-DEFINITION MEDIA DOWNLOADER ENGINE

## OBJECTIVE

Build an unblockable, 100% free, production-grade Local Web Application running on PC Desktop (`http://localhost:8000`). The system extracts and downloads images/videos from Instagram, X (Twitter), TikTok, YouTube, Facebook, and Reddit in maximum native resolution (HD/4K) with zero quality loss.

---

## ARCHITECTURE & DIRECTORY STRUCTURE (CLEAN ARCHITECTURE)

Strictly enforce separation of concerns across the following structure:

- `src/domain/`: Pydantic data schemas (`models.py`) and custom domain exceptions (`exceptions.py`).
- `src/use_cases/`: Core business logic orchestrators:
  - `download_media.py`: 4-Tier Fallback Cascade execution logic.
  - `batch_processor.py`: Concurrent multi-threaded download queue manager.
  - `local_storage.py`: Output file naming, folder creation, and OS pathing.
- `src/infrastructure/`: Low-level platform drivers and adapters:
  - `ytdlp_engine.py`: Tier 1 Fast-Path non-rendered extractor.
  - `playwright_sniffer.py`: Tier 2 Stealth Network Interceptor (GraphQL/REST API sniffer).
  - `local_cookie_manager.py`: Tier 3 Browser cookie bridge for private/restricted posts.
  - `ffmpeg_merger.py`: Tier 4 Lossless video/audio stream remuxer (`-c copy`).
  - `os_system_adapter.py`: OS File Explorer trigger (`explorer.exe` / `open` / `xdg-open`).
- `src/presentation/`:
  - `web_server.py`: FastAPI application serving REST API and WebSocket endpoints.
  - `websocket_manager.py`: Real-time download progress and speed broadcaster.
  - `static/`: HTML5/Tailwind CSS Single Page Application (`index.html`, `app.js`, `style.css`).
- `downloads/`: Default output storage directory.
- `main.py`: Application entry point with automatic browser launch trigger.

---

## 4-TIER FALLBACK CASCADE ENGINE

Implement cascading execution inside `src/use_cases/download_media.py`. If Tier N fails or returns low quality, automatically fall back to Tier N+1:

1. **Tier 1 (Fast-Path `yt-dlp`):** Immediate extraction without browser rendering using format rule `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best`.
2. **Tier 2 (Stealth Network Interceptor `Playwright`):** Triggered on HTTP 429/403 or Login Walls. Launches headless Chromium with stealth patches, listens to `page.on("response")` network events, and sniffs raw GraphQL/REST JSON payloads for source CDN URLs.
3. **Tier 3 (Local Cookie Bridge):** Injects user's local Chrome/Firefox session cookies to bypass login walls on private posts.
4. **Tier 4 (Stream Remuxer `FFmpeg`):** Combines separate 4K video and audio streams into a single `.mp4` container using `-c copy` (zero quality loss, hardware accelerated).

---

## LOCAL DESKTOP & WEB UX SPECIFICATIONS

- **Auto Browser Launch:** `main.py` automatically opens `http://localhost:8000` in the default system browser upon startup.
- **Real-Time WebSockets:** Broadcast percentage, download speed (MB/s), ETA, and status to the UI.
- **Batch Processing Queue:** Support pasting multi-line URLs and concurrent background downloads.
- **Clipboard Auto-Detect Listener:** Detect copied social media URLs in clipboard and offer 1-click auto-fill.
- **Native OS File Explorer Trigger:** "Open Downloads Folder" button opens system File Explorer directly.

---

## AGENT INSTRUCTIONS

1. Generate all folders and files strictly adhering to Clean Architecture layout.
2. Embed clean, professional inline comments explaining complex logic steps for team development.
3. Add robust error handling for rate limits, dead CDN links, and network timeouts.
4. Provide a populated `requirements.txt` containing `fastapi`, `uvicorn`, `playwright`, `playwright-stealth`, `yt-dlp`, and `pydantic`.
