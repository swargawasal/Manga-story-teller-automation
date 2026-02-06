# voice_memory.py - Persistent Character Voice Mapping
import binascii
import json
import os
from config.config import TEMP_DIR

# Pool of available edge-tts voices (multi-language/tone)
VOICE_POOL = [
    "en-US-GuyNeural",
    "en-US-JennyNeural",
    "en-GB-RyanNeural",
    "en-GB-SoniaNeural",
    "en-AU-LiamNeural",
    "en-AU-NatashaNeural",
    "en-US-ChristopherNeural",
    "en-US-MichelleNeural",
]

class VoiceMemory:
    def __init__(self, storage_path=None):
        if storage_path is None:
            storage_path = os.path.join(TEMP_DIR, "voice_memory.json")
        self.storage_path = storage_path
        self.memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_memory(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.memory, f, indent=4)

    def get_voice(self, character_name: str) -> str:
        """
        Retrieves or assigns a deterministic voice for a character.
        Assignment is based on CRC32(character_name) % len(VOICE_POOL).
        """
        character_name = character_name.lower().strip()
        if character_name in self.memory:
            return self.memory[character_name]

        # Deterministic assignment
        crc = binascii.crc32(character_name.encode('utf-8')) & 0xffffffff
        voice_index = crc % len(VOICE_POOL)
        assigned_voice = VOICE_POOL[voice_index]

        self.memory[character_name] = assigned_voice
        self._save_memory()
        return assigned_voice
