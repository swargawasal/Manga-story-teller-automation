"""
Visual Enhancement Module - Tier-1 Production-Safe
Real-CUGAN 2× upscaling with hash-based caching.
"""
import os
import cv2
import hashlib
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class VisualEnhancer:
    """
    Production-safe visual enhancement using Real-CUGAN 2× upscaling.
    
    Key features:
    - Hash-based caching (bulletproof)
    - Line art preservation
    - No face redrawing
    - Deterministic output
    """
    
    def __init__(self, cache_dir: str = "cache/upscaled"):
        """
        Initialize visual enhancer.
        
        Args:
            cache_dir: Directory for cached upscaled panels
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self._upscaler = None
        self._cache: Dict[str, str] = {}
        
        logger.info("✅ VisualEnhancer initialized (Real-CUGAN 2×)")
    
    @property
    def upscaler(self):
        """Lazy load Real-CUGAN model."""
        if self._upscaler is None:
            try:
                from realcugan_ncnn_vulkan_python import Realcugan
                self._upscaler = Realcugan(
                    gpuid=0,      # Use GPU 0
                    scale=2,      # 2× upscaling (not 4×)
                    noise=0       # No denoising (preserve line art)
                )
                logger.info("✅ Real-CUGAN model loaded (2× scale)")
            except ImportError:
                logger.error("❌ Real-CUGAN not installed. Run: pip install realcugan-ncnn-vulkan-python")
                raise
        return self._upscaler
    
    def _hash_file(self, path: str) -> str:
        """
        Generate MD5 hash of file content.
        
        CRITICAL: Use content hash, NOT file path, for cache key.
        This prevents wrong reuse if same path has different content.
        
        Args:
            path: Path to file
            
        Returns:
            MD5 hash of file content
        """
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def upscale_panel(self, panel_path: str, force: bool = False) -> str:
        """
        Upscale manga panel 2× with hash-based caching.
        
        Args:
            panel_path: Path to manga panel
            force: Force re-upscaling (skip cache)
            
        Returns:
            Path to upscaled panel
        """
        # Generate cache key from file content hash
        cache_key = self._hash_file(panel_path)
        
        # Check cache
        if not force and cache_key in self._cache:
            cached_path = self._cache[cache_key]
            if os.path.exists(cached_path):
                logger.debug(f"✅ Using cached upscaled panel: {cache_key[:8]}")
                return cached_path
        
        # Load panel
        panel = cv2.imread(panel_path)
        if panel is None:
            logger.error(f"❌ Failed to load panel: {panel_path}")
            return panel_path  # Return original on failure
        
        # Upscale with Real-CUGAN
        logger.info(f"🎨 Upscaling panel 2× (Real-CUGAN): {os.path.basename(panel_path)}")
        
        try:
            upscaled = self.upscaler.process(panel)
        except Exception as e:
            logger.error(f"❌ Real-CUGAN failed: {e}")
            return panel_path  # Soft fallback to original
        
        # Save upscaled panel
        output_path = os.path.join(self.cache_dir, f"{cache_key}.jpg")
        cv2.imwrite(output_path, upscaled, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # Update cache
        self._cache[cache_key] = output_path
        
        logger.info(f"✅ Upscaled: {panel.shape} → {upscaled.shape}")
        
        return output_path
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Cache stats (hits, size, etc.)
        """
        cache_size = sum(
            os.path.getsize(os.path.join(self.cache_dir, f))
            for f in os.listdir(self.cache_dir)
            if os.path.isfile(os.path.join(self.cache_dir, f))
        )
        
        return {
            "cached_panels": len(self._cache),
            "cache_size_mb": cache_size / (1024 * 1024),
            "cache_dir": self.cache_dir
        }
    
    def clear_cache(self):
        """Clear upscaling cache."""
        import shutil
        shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self._cache.clear()
        logger.info("🗑️ Upscaling cache cleared")
