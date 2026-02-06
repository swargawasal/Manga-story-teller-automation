"""
Frame Interpolation Module - Tier-1 Production-Safe
Selective RIFE 48 FPS interpolation with mandatory guards.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FrameInterpolator:
    """
    Production-safe frame interpolation using RIFE v4.6.
    
    Key features:
    - Selective interpolation (only moving scenes)
    - 48 FPS target (not 60)
    - Duration threshold guard
    - Soft fallback on failure
    """
    
    def __init__(self):
        """Initialize frame interpolator."""
        self._rife = None
        logger.info("✅ FrameInterpolator initialized (RIFE v4.6, selective 48 FPS)")
    
    @property
    def rife(self):
        """Lazy load RIFE model."""
        if self._rife is None:
            try:
                from rife_ncnn_vulkan_python import Rife
                self._rife = Rife(
                    gpuid=0,
                    model='rife-v4.6',
                    tta_mode=False,
                    tta_temporal_mode=False,
                    uhd_mode=False,
                    num_threads=2
                )
                logger.info("✅ RIFE v4.6 model loaded")
            except ImportError:
                logger.error("❌ RIFE not installed. Run: pip install rife-ncnn-vulkan-python")
                raise
        return self._rife
    
    def should_interpolate(self, camera_action: str, duration: float) -> bool:
        """
        Determine if scene should be interpolated.
        
        GUARD #1: Scene duration threshold
        Never interpolate very short scenes (< 1.2s).
        RIFE artifacts are more visible on short clips.
        
        Args:
            camera_action: Camera action type
            duration: Scene duration in seconds
            
        Returns:
            True if should interpolate
        """
        # Guard: Skip very short scenes
        if duration < 1.2:
            logger.debug(f"⏭️ Skipping interpolation: scene too short ({duration:.1f}s)")
            return False
        
        # Only interpolate moving scenes
        moving_actions = ['zoom_in', 'zoom_out', 'shake', 'pan_left', 'pan_right']
        
        if camera_action not in moving_actions:
            logger.debug(f"⏭️ Skipping interpolation: static scene ({camera_action})")
            return False
        
        return True
    
    def interpolate_to_48fps(
        self,
        video_path: str,
        camera_action: str,
        duration: float
    ) -> str:
        """
        Interpolate video from 30 FPS to 48 FPS.
        
        GUARD #2: Soft fallback on RIFE failure (NON-NEGOTIABLE)
        If RIFE fails, return original video to preserve stability.
        
        Args:
            video_path: Path to 30 FPS video
            camera_action: Camera action type
            duration: Scene duration in seconds
            
        Returns:
            Path to 48 FPS video (or original if skipped/failed)
        """
        # Check if should interpolate
        if not self.should_interpolate(camera_action, duration):
            return video_path
        
        output_path = video_path.replace('.mp4', '_48fps.mp4')
        
        # GUARD #2: Soft fallback on failure
        try:
            logger.info(f"⚡ Interpolating to 48 FPS: {os.path.basename(video_path)}")
            
            # Use FFmpeg + RIFE for interpolation
            import subprocess
            
            # Extract frames at 30 FPS
            frames_dir = video_path.replace('.mp4', '_frames')
            os.makedirs(frames_dir, exist_ok=True)
            
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-vf', 'fps=30',
                f'{frames_dir}/frame_%04d.png'
            ], check=True, capture_output=True)
            
            # Get frame list
            import glob
            frames = sorted(glob.glob(f'{frames_dir}/frame_*.png'))
            
            if len(frames) < 2:
                logger.warning("⚠️ Not enough frames for interpolation")
                return video_path
            
            # Interpolate frames with RIFE
            interpolated_dir = video_path.replace('.mp4', '_interpolated')
            os.makedirs(interpolated_dir, exist_ok=True)
            
            frame_idx = 0
            for i in range(len(frames) - 1):
                # Read frames
                import cv2
                frame1 = cv2.imread(frames[i])
                frame2 = cv2.imread(frames[i + 1])
                
                # Save original frame
                cv2.imwrite(f'{interpolated_dir}/frame_{frame_idx:04d}.png', frame1)
                frame_idx += 1
                
                # Generate intermediate frame (30 → 48 FPS = 1.6× = 1 intermediate frame per 2 original)
                if i % 2 == 0:
                    try:
                        intermediate = self.rife.process(frame1, frame2)
                        cv2.imwrite(f'{interpolated_dir}/frame_{frame_idx:04d}.png', intermediate)
                        frame_idx += 1
                    except Exception as e:
                        logger.warning(f"⚠️ RIFE frame interpolation failed: {e}")
                        # Continue without this intermediate frame
            
            # Save last frame
            cv2.imwrite(f'{interpolated_dir}/frame_{frame_idx:04d}.png', cv2.imread(frames[-1]))
            
            # Encode to video at 48 FPS
            subprocess.run([
                'ffmpeg', '-framerate', '48',
                '-i', f'{interpolated_dir}/frame_%04d.png',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-crf', '18',
                output_path
            ], check=True, capture_output=True)
            
            # Cleanup
            import shutil
            shutil.rmtree(frames_dir)
            shutil.rmtree(interpolated_dir)
            
            logger.info(f"✅ Interpolated to 48 FPS: {os.path.basename(output_path)}")
            
            return output_path
            
        except Exception as e:
            # MANDATORY: Soft fallback on any failure
            logger.warning(f"⚠️ RIFE interpolation failed, falling back to 30 FPS: {e}")
            return video_path  # Preserve stability - return original
    
    def get_stats(self) -> dict:
        """
        Get interpolation statistics.
        
        Returns:
            Interpolation stats
        """
        return {
            "model": "RIFE v4.6",
            "target_fps": 48,
            "selective": True,
            "min_duration": 1.2
        }
