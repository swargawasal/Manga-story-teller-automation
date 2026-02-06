# voiceover.py - edge-tts implementation
import os
import asyncio
import edge_tts
from config import TEMP_DIR

class VoiceoverEngine:
    def __init__(self):
        pass

    async def _amake_voiceover(self, text: str, voice: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def generate_voiceover(self, text: str, voice: str, output_filename: str) -> str:
        """
        Synchronous wrapper for generating VO using edge-tts.
        """
        output_path = os.path.join(TEMP_DIR, output_filename)
        asyncio.run(self._amake_voiceover(text, voice, output_path))
        return output_path
