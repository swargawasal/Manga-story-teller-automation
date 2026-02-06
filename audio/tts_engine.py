# tts_engine.py - edge-tts implementation with Audio Normalization
import os
import asyncio
import subprocess
import edge_tts
from config.config import TEMP_DIR

class TTSEngine:
    def __init__(self):
        pass

    async def _amake_voiceover(self, text: str, voice: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def _apply_audio_processing(self, input_path: str, output_path: str):
        """
        Extracted logic from audio_processing.py:
        Removes noise, adds bass/treble boost, compression, and YouTube-safe loudnorm.
        """
        # YouTube-safe loudness normalization filter
        loudnorm_filter = "loudnorm=I=-14:TP=-1.5:LRA=11"
        
        # Audio Effects Chain: EQ -> Compression -> Normalization
        # Optimized for narration/dialogue
        effects = [
            "equalizer=f=80:t=h:w=100:g=3",     # Slight bass boost
            "equalizer=f=12000:t=h:w=2000:g=2",   # Slight air
            "acompressor=threshold=-14dB:ratio=2.5:attack=20:release=200", # Glue
            "alimiter=limit=0.95",              # Safety ceiling
            loudnorm_filter
        ]
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", ",".join(effects),
            "-ac", "2", "-ar", "44100",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Audio processing failed: {e.stderr.decode()[:100]}")
            return False

    def generate_voiceover(self, text: str, voice: str, filename: str) -> str:
        """
        Generates VO using edge-tts and applies normalization.
        """
        raw_path = os.path.join(TEMP_DIR, f"raw_{filename}")
        processed_path = os.path.join(TEMP_DIR, filename)
        
        # 1. Generate Raw TTS
        asyncio.run(self._amake_voiceover(text, voice, raw_path))
        
        # 2. Apply Normalization/Improvement
        if self._apply_audio_processing(raw_path, processed_path):
            if os.path.exists(raw_path):
                os.remove(raw_path)
            return processed_path
        
        # Fallback to raw if processing fails
        return raw_path

    def generate_narration(self, text: str, filename: str) -> str:
        """
        Generates narration using configured narrator voice.
        Uses narrator-specific settings from config.
        
        Args:
            text: Narration text to synthesize
            filename: Output filename (e.g., "narration_1.mp3")
            
        Returns:
            Path to generated narration audio file
        """
        from config.config import NARRATOR_VOICE, NARRATOR_RATE, NARRATOR_PITCH, NARRATOR_VOLUME
        
        raw_path = os.path.join(TEMP_DIR, f"raw_{filename}")
        processed_path = os.path.join(TEMP_DIR, filename)
        
        # 1. Generate Raw TTS with narrator voice
        asyncio.run(self._amake_voiceover(text, NARRATOR_VOICE, raw_path))
        
        # 2. Apply narrator-specific audio processing
        if self._apply_narrator_processing(raw_path, processed_path, NARRATOR_VOLUME):
            if os.path.exists(raw_path):
                os.remove(raw_path)
            return processed_path
        
        # Fallback to raw if processing fails
        return raw_path
    
    def _apply_narrator_processing(self, input_path: str, output_path: str, volume: float) -> bool:
        """
        Narrator-specific audio processing.
        Optimized for clear, authoritative narration.
        """
        # Narrator-optimized loudness normalization
        loudnorm_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"
        
        # Narrator Effects Chain: Clarity + Presence + Authority
        effects = [
            "highpass=f=80",                        # Remove rumble
            "equalizer=f=200:t=h:w=100:g=2",        # Warmth
            "equalizer=f=3000:t=h:w=1000:g=3",      # Presence/clarity
            "acompressor=threshold=-18dB:ratio=3:attack=5:release=150",  # Smooth compression
            "alimiter=limit=0.95",                  # Safety ceiling
            loudnorm_filter,
            f"volume={volume}"                      # Apply configured volume
        ]
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", ",".join(effects),
            "-ac", "2", "-ar", "44100",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Narrator audio processing failed: {e.stderr.decode()[:100]}")
            return False
