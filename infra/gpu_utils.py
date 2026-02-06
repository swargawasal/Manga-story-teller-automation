# gpu_utils.py - General GPU Detection and Memory Management
import os
import logging
import gc
import time

logger = logging.getLogger("gpu_utils")

# Lazy torch import
torch = None

def get_torch():
    global torch
    if torch is None:
        try:
            import torch
        except ImportError:
            return None
    return torch

def get_gpu_status():
    """Returns basic GPU health status."""
    t = get_torch()
    if t and t.cuda.is_available():
        try:
            free, total = t.cuda.mem_get_info()
            return {
                "available": True,
                "device": t.cuda.get_device_name(0),
                "free_mb": free // 1024 // 1024,
                "total_mb": total // 1024 // 1024
            }
        except:
            return {"available": True, "device": "Unknown", "free_mb": 0, "total_mb": 0}
    return {"available": False, "device": "None", "free_mb": 0, "total_mb": 0}

def clear_gpu_cache():
    """Aggressively clears GPU memory."""
    t = get_torch()
    if t and t.cuda.is_available():
        t.cuda.empty_cache()
    gc.collect()
    logger.info("🗑️ GPU memory cleared.")

def run_with_gpu_guard(func, *args, **kwargs):
    """
    Runs a function with GPU memory clearing and OOM protection.
    Used for OCR and Panel Detection.
    """
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "out of memory" in str(e).lower():
                logger.warning(f"⚠️ GPU OOM detected (Attempt {attempt+1}). Clearing cache...")
                clear_gpu_cache()
                if attempt == max_retries:
                    logger.error("❌ GPU OOM persistent after retries.")
                    raise e
                time.sleep(2)
            else:
                raise e
