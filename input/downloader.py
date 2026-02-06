# downloader.py - Mature Manga/Comic Input & yt-dlp Processor
import os
import logging
import yt_dlp
import glob
import time
from datetime import datetime
import re
import json
import hashlib
import shutil
import requests
import subprocess
from typing import Dict, Optional, List
from processing.pdf_processor import process_pdf
from config.config import TEMP_DIR, DOWNLOAD_DIR

logger = logging.getLogger("downloader")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configuration & Constants
DOWNLOAD_RETRY_DELAY = int(os.getenv("DOWNLOAD_RETRY_DELAY", 2))
RATE_LIMIT_WAIT = int(os.getenv("RATE_LIMIT_WAIT", 8))

def _calculate_file_hash(path: str) -> str:
    """Calculate SHA1 hash of file for uniqueness."""
    try:
        sha1 = hashlib.sha1()
        with open(path, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data: break
                sha1.update(data)
        return sha1.hexdigest()[:8]
    except:
        return ""

class DownloadIndex:
    """Persistent, lightweight index for O(1) duplicate lookups."""
    INDEX_FILE = os.path.join(DOWNLOAD_DIR, "index.json")
    
    @classmethod
    def _load_index(cls) -> Dict:
        try:
            if os.path.exists(cls.INDEX_FILE):
                with open(cls.INDEX_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except: pass
        return {"ids": {}, "hashes": {}}

    @classmethod
    def _save_index(cls, data: Dict):
        temp = cls.INDEX_FILE + ".tmp"
        try:
            with open(temp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=0)
            if os.path.exists(cls.INDEX_FILE): os.remove(cls.INDEX_FILE)
            os.rename(temp, cls.INDEX_FILE)
        except: pass

    @classmethod
    def register(cls, path: str, url_id: str = None, c_hash: str = None):
        data = cls._load_index()
        if url_id: data["ids"][str(url_id)] = path
        if c_hash: data["hashes"][c_hash] = path
        cls._save_index(data)

    @classmethod
    def find_by_id(cls, url_id: str) -> Optional[str]:
        data = cls._load_index()
        path = data["ids"].get(str(url_id))
        return path if path and os.path.exists(path) else None

def process_manga_input(input_path: str) -> List[str]:
    """
    Main entry point for pipeline input.
    Accepts: Local PDF, Local Image, or URL.
    """
    # 1. Handle URL
    if input_path.startswith("http"):
        # Check index first
        existing = DownloadIndex.find_by_id(input_path)
        if existing: return [existing]
        
        print(f"🌐 Fetching URL: {input_path}")
        ext = input_path.split('.')[-1].split('?')[0].lower()
        if ext not in ['png', 'jpg', 'jpeg', 'pdf']: ext = 'png'
        
        filename = f"manga_{int(time.time())}.{ext}"
        path = os.path.join(DOWNLOAD_DIR, filename)
        
        try:
            response = requests.get(input_path, stream=True, timeout=30)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in response.iter_content(1024): f.write(chunk)
                
                # Register in index
                DownloadIndex.register(path, url_id=input_path)
                
                if ext == 'pdf':
                    return process_pdf(path)
                return [path]
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return []

    # 2. Handle PDF
    if input_path.lower().endswith(".pdf"):
        return process_pdf(input_path)

    # 3. Handle Local Image
    if os.path.exists(input_path):
        return [input_path]

    raise ValueError(f"Invalid input source: {input_path}")

# Keep legacy yt-dlp downloader for social/video expansion if needed
def download_video(url: str, custom_title: str = None) -> str:
    """Legacy yt-dlp downloader preserved for infrastructure reuse."""
    # Simplified version for now, but keeping the signature and core logic
    opts = {'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'), 'quiet': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)
