import os
import subprocess
import math
from typing import List, Dict, Optional
from config.config import FPS, WIDTH, HEIGHT

# ==================== RULE TABLES ====================
# emotion -> camera_mode
EMOTION_TO_CAMERA = {
    "CALM": "STATIC",
    "HAPPY": "ZOOM_IN",
    "ANGRY": "SHAKE",
    "SAD": "PAN_LEFT",
    "SURPRISED": "ZOOM_OUT",
    "FIGHT": "SHAKE_AGRESSIVE",
    "DRAMATIC": "ZOOM_IN_FAST",
    "UNKNOWN": "STATIC"
}

# camera_mode -> FFmpeg filter template
# {frames} is computed in Python: ceil(duration * FPS)
# {fps} is config.FPS
# {w}, {h} are config.WIDTH, config.HEIGHT
# Clamping applied to crop coordinates to prevent negative values
CAMERA_TO_FILTER = {
    "STATIC": (
        "scale={w}:{h}:force_original_aspect_ratio=decrease,"
        "pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
        "fps={fps}"
    ),
    "ZOOM_IN": (
        "scale=2500:-1,"
        "zoompan=z='min(zoom+0.001,1.5)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h},"
        "fps={fps}"
    ),
    "ZOOM_OUT": (
        "scale=2500:-1,"
        "zoompan=z='max(1.5-0.001*on,1.0)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h},"
        "fps={fps}"
    ),
    "PAN_LEFT": (
        "scale=-1:{h},"
        "crop={w}:{h}:'max(0, min(iw-{w}, (iw-{w})*n/{frames}))':0,"
        "fps={fps}"
    ),
    "PAN_RIGHT": (
        "scale=-1:{h},"
        "crop={w}:{h}:'max(0, min(iw-{w}, (iw-{w})*(1-n/{frames})))':0,"
        "fps={fps}"
    ),
    "SHAKE": (
        "scale=2000:-1,"
        "crop={w}:{h}:'max(0, min(iw-{w}, (iw-{w})/2+15*sin(2*PI*n/({fps}*0.15))))':'max(0, min(ih-{h}, (ih-{h})/2+15*cos(2*PI*n/({fps}*0.15))))',"
        "fps={fps}"
    ),
    "SHAKE_AGRESSIVE": (
        "scale=2000:-1,"
        "crop={w}:{h}:'max(0, min(iw-{w}, (iw-{w})/2+40*sin(2*PI*n/({fps}*0.1))))':'max(0, min(ih-{h}, (ih-{h})/2+40*cos(2*PI*n/({fps}*0.1))))',"
        "fps={fps}"
    ),
    "ZOOM_IN_FAST": (
        "scale=2500:-1,"
        "zoompan=z='min(zoom+0.005,1.5)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h},"
        "fps={fps}"
    )
}

def get_audio_duration(audio_path: str) -> float:
    """Helper to get duration via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 5.0 # Fallback

def get_camera_timing(emotion: str, duration: float) -> Dict:
    """
    Returns camera timing information for SFX synchronization.
    
    Args:
        emotion: Scene emotion (e.g., "ANGRY", "CALM")
        duration: Scene duration in seconds
        
    Returns:
        {
            "action": str,  # Camera mode (e.g., "shake", "zoom_in")
            "duration": float,
            "intensity": str  # "low"|"medium"|"high"
        }
    """
    camera_mode = EMOTION_TO_CAMERA.get(emotion.upper(), "STATIC")
    
    # Determine intensity based on camera mode
    intensity_map = {
        "STATIC": "low",
        "ZOOM_IN": "medium",
        "ZOOM_OUT": "medium",
        "PAN_LEFT": "low",
        "PAN_RIGHT": "low",
        "SHAKE": "high",
        "SHAKE_AGRESSIVE": "high",
        "ZOOM_IN_FAST": "high"
    }
    
    return {
        "action": camera_mode.lower(),
        "duration": duration,
        "intensity": intensity_map.get(camera_mode, "low")
    }

def generate_animation_command(
    image_path: str,
    audio_path: str,
    output_path: str,
    emotion: str = "CALM"
) -> List[str]:
    """
    Generates a deterministic FFmpeg command to animate a static image.
    Uses global settings from config.py.
    """
    duration = get_audio_duration(audio_path)
    # MANDATORY: Compute frame count in Python
    frames = math.ceil(duration * FPS)
    
    camera_mode = EMOTION_TO_CAMERA.get(emotion.upper(), "STATIC")
    filter_template = CAMERA_TO_FILTER.get(camera_mode, CAMERA_TO_FILTER["STATIC"])
    
    # Inject variables into filter string
    vf_filter = filter_template.format(
        frames=frames,
        fps=FPS, 
        w=WIDTH, 
        h=HEIGHT
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-t", f"{duration:.3f}",
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),  # MANDATORY: Enforce output FPS
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]
    
    return cmd
