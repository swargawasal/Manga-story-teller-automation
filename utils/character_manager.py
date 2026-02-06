"""
Character Asset Manager
Auto-creates character folders when new characters are detected.
"""
import os
from typing import List

class CharacterAssetManager:
    """Manages character audio asset directories."""
    
    def __init__(self, base_dir: str = "assets/characters"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def ensure_character_folders(self, character_name: str) -> dict:
        """
        Auto-create character folders if new character detected.
        
        Args:
            character_name: Character name (will be lowercased)
            
        Returns:
            {
                "character": str,
                "is_new": bool,
                "attacks_dir": str,
                "personality_dir": str
            }
        """
        character_name = character_name.lower().strip()
        character_dir = os.path.join(self.base_dir, character_name)
        attacks_dir = os.path.join(character_dir, "attacks")
        
        is_new = not os.path.exists(character_dir)
        
        if is_new:
            # Create only attacks directory (narrator handles personality)
            os.makedirs(attacks_dir, exist_ok=True)
            
            print(f"\n{'='*60}")
            print(f"🆕 NEW CHARACTER DETECTED: {character_name.upper()}")
            print(f"{'='*60}")
            print(f"✅ Created: {character_dir}/")
            print(f"   └── attacks/")
            print(f"\n💡 Add attack audio when ready:")
            print(f"   - Attack SFX: {attacks_dir}/{{attack_name}}.wav")
            print(f"   - If no audio → Narrator describes attack by name")
            print(f"{'='*60}\n")
        
        return {
            "character": character_name,
            "is_new": is_new,
            "attacks_dir": attacks_dir
        }
    
    def ensure_all_character_folders(self, character_names: List[str]) -> List[dict]:
        """
        Ensure folders exist for multiple characters.
        
        Args:
            character_names: List of character names
            
        Returns:
            List of character folder info dicts
        """
        results = []
        for name in character_names:
            if name and name.strip():
                result = self.ensure_character_folders(name)
                results.append(result)
        return results
    
    def list_characters(self) -> List[str]:
        """
        List all characters with existing folders.
        
        Returns:
            List of character names
        """
        if not os.path.exists(self.base_dir):
            return []
        
        characters = []
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item != "README.md":
                characters.append(item)
        
        return sorted(characters)
    
    def get_character_assets(self, character_name: str) -> dict:
        """
        Get all audio assets for a character.
        
        Args:
            character_name: Character name
            
        Returns:
            {
                "attacks": List[str]  # Attack audio files
            }
        """
        character_name = character_name.lower().strip()
        character_dir = os.path.join(self.base_dir, character_name)
        
        attacks = []
        
        attacks_dir = os.path.join(character_dir, "attacks")
        if os.path.exists(attacks_dir):
            for file in os.listdir(attacks_dir):
                if file.endswith(('.wav', '.mp3')):
                    attacks.append(os.path.splitext(file)[0])
        
        return {
            "attacks": sorted(attacks)
        }
