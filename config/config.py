# config/config.py - Production Configuration for Manga Pipeline
import os
from dotenv import load_dotenv

# Load .env from root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ==================== DIRECTORY STRUCTURE ====================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMP_DIR = os.path.join(BASE_DIR, "runtime", "temp")
OUTPUT_DIR = os.path.join(BASE_DIR, "runtime", "output")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "runtime", "downloads")
MODELS_DIR = os.path.join(BASE_DIR, "runtime", "models")

# Ensure runtime directories exist
for d in [TEMP_DIR, OUTPUT_DIR, DOWNLOAD_DIR, MODELS_DIR]:
    os.makedirs(d, exist_ok=True)

# ==================== VIDEO SETTINGS ====================
FPS = int(os.getenv("BOT_FPS", 24))
WIDTH = int(os.getenv("WIDTH", 1920))
HEIGHT = int(os.getenv("HEIGHT", 1080))

# ==================== AI & REASONING ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# ==================== COMIC SPECIFIC ====================
PANEL_CONFIDENCE_THRESHOLD = float(os.getenv("PANEL_CONFIDENCE_THRESHOLD", 0.5))
OCR_LANGUAGES = ['en']
VOICE_MEMORY_PATH = os.path.join(TEMP_DIR, "voice_memory.json")
MUSIC_VOLUME = float(os.getenv("MUSIC_VOLUME", 0.15))

# FFmpeg Paths
FFMPEG_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_BIN", "ffprobe")

# GPU Settings
USE_GPU = os.getenv("GPU_MODE", "auto").lower() != "off"

# ==================== NARRATION SETTINGS ====================
NARRATOR_ENABLED = os.getenv("NARRATOR_ENABLED", "true").lower() == "true"
NARRATOR_VOICE = os.getenv("NARRATOR_VOICE", "en-US-GuyNeural")
NARRATOR_RATE = os.getenv("NARRATOR_RATE", "0%")
NARRATOR_PITCH = os.getenv("NARRATOR_PITCH", "0%")
NARRATOR_VOLUME = float(os.getenv("NARRATOR_VOLUME", 0.8))
