<div align="center">

<img src="assets/banner.png" alt="CLINK Banner" width="100%">

# 🌌 CLINK

**The Ultimate Universal Media Downloader & Enhancer**

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blueviolet?style=for-the-badge&logo=appveyor" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Maintained_by-Lanciuy-ff69b4?style=for-the-badge" alt="Author">
</p>

[**Features**](#-core-features) • [**How it Works**](#-4-tier-cascade-engine) • [**Installation**](#-quick-start) • [**Usage**](#-usage-guide) • [**Security**](#-privacy-first)

</div>

---

## ⚡ The Concept
**CLINK** is not just another downloader. Built by **Lanciuy**, CLINK is a hyper-optimized, multi-threaded local application designed to extract native-resolution videos, audio, and images from *any* major social platform. 

Whether it's a hidden Instagram Reel, a Twitter Video, or a full YouTube Playlist, CLINK gets it. If the image is blurry? CLINK uses local AI to upscale and enhance it automatically. 

---

## 🚀 Core Features

- **🌐 Universal Compatibility**: Supports YouTube, Instagram, X (Twitter), TikTok, Reddit, Facebook, and thousands of other sites.
- **🤖 AI Image Enhancement**: Built-in integration with **Real-ESRGAN** (`realesrgan-x4plus`) + Pillow *Unsharp Masking* to upscale low-res photos and restore facial pores and hair details.
- **🎵 Format Extraction**: Choose between Best Video (MP4) or Audio Only (MP3) extraction.
- **📂 Playlist Support**: Paste a playlist or profile link to instantly grab all contained media concurrently.
- **🛡️ 4-Tier Fallback Cascade**: If a platform tries to block the download, CLINK automatically shifts through 4 different extraction engines (including native Cookie bridging and Playwright Stealth Sniffing) until it succeeds.
- **💻 Local & Private**: CLINK runs 100% on your machine. No cloud servers, no data leaks, and absolute privacy.

---

## ⚙️ 4-Tier Cascade Engine

Clink uses an advanced fallback architecture to guarantee downloads:

| Tier | Engine | Description |
| :--- | :--- | :--- |
| **Tier 1** | `Fast-Path` | Direct API extraction using optimized yt-dlp. Fastest, but vulnerable to login walls. |
| **Tier 2** | `Cookie Bridge` | Re-attempts extraction using your local `cookies.txt` to bypass private accounts and login walls. |
| **Tier 3** | `Playwright Stealth` | Spawns a headless browser to intercept raw CDN network traffic for dynamically rendered blobs. |
| **Tier 4** | `Remuxing (FFmpeg)`| Downloads raw video and audio streams separately and forcefully stitches them locally. |

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.10+
- FFmpeg (Must be installed and added to your System PATH)

### 2. Installation
Clone the repository and install the dependencies:

```bash
git clone https://github.com/Lanciuy/CLINK.git
cd CLINK
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```
*The sleek Glassmorphism web interface will automatically open at `http://localhost:8000`.*

---

## 📖 Usage Guide

### Standard Download
1. Open the CLINK Web Interface.
2. Paste your URL(s) into the neon input box. (Supports multiple URLs separated by newlines).
3. Click **Analyze Media**.
4. Select the media you want from the generated grid and click **Download**.

### Downloading Private / Login-Walled Posts (e.g., Instagram)
If a post requires you to be logged in:
1. Install the [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpocnjcndcbnb) extension on Chrome.
2. Go to Instagram/Twitter and click the extension to copy your cookies.
3. In CLINK, click **Advanced Settings**.
4. Paste the cookies into the *Authentication Cookies* box and click **Save Cookies**.
5. Analyze and download as normal!

### AI Image Upscaling
Check the **Enhance Photos (AI Upscale)** box before clicking Download. CLINK will automatically route all downloaded images through the local GPU-accelerated Real-ESRGAN engine.

---

## 🔒 Privacy First
Created with absolute privacy in mind. **CLINK never phones home.** 
Your cookies, your downloaded files, and your browsing habits remain entirely on your local machine. No tracking, no analytics, no nonsense.

---

<div align="center">
  <p><b>Crafted with ❤️ by Lanciuy</b></p>
  <p><i>Empowering your local media library.</i></p>
</div>
