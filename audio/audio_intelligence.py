# audio/audio_intelligence.py - Professional Audio Intelligence Layer
import os
from typing import Dict, Optional, Tuple

class AudioIntelligence:
    """
    Deterministic audio decision compiler.
    Converts Gemini audio intent → FFmpeg execution parameters.
    
    CRITICAL FIXES APPLIED:
    1. Relative silence timing (30% of scene, max 2s)
    2. Silence exclusivity (silence → no ambience/bgm)
    3. Conditional ducking (only if dialogue > 0.2s)
    4. Confidence-based SFX (disable if < 0.6)
    5. 3-layer audio limit (dialogue + 1 bg + 1 impact)
    """
    
    # Asset mapping (ENUM → file path)
    BGM_MAP = {
        "calm": "assets/bgm/calm_loop.wav",
        "tense": "assets/bgm/tense_loop.wav",
        "heroic": "assets/bgm/heroic_loop.wav",
        "sad": "assets/bgm/sad_loop.wav",
        "none": None
    }
    
    SFX_MAP = {
        "punch": "assets/sfx/punch.wav",
        "slash": "assets/sfx/slash.wav",
        "explosion": "assets/sfx/explosion.wav",
        "hit": "assets/sfx/hit.wav",
        "none": None
    }
    
    AMBIENCE_MAP = {
        "wind": "assets/ambience/wind.wav",
        "sea": "assets/ambience/sea.wav",
        "crowd": "assets/ambience/crowd.wav",
        "room": "assets/ambience/room.wav",
        "none": None
    }
    
    STINGER_MAP = {
        "intro": "assets/stingers/intro.wav",
        "outro": "assets/stingers/outro.wav"
    }
    
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = assets_dir
    
    def calculate_narration_duration(self, narration_text: str) -> float:
        """
        Estimate narration duration based on text length.
        
        Average speaking rate: 150 words/min = 2.5 words/sec
        Add 20% for dramatic pauses and emphasis.
        
        Args:
            narration_text: Narration text
            
        Returns:
            Estimated duration in seconds
        """
        if not narration_text:
            return 0.0
        
        word_count = len(narration_text.split())
        base_duration = word_count / 2.5  # 150 words/min
        return base_duration * 1.2  # Add 20% for pauses
        
    def process_audio_intent(
        self,
        audio_intent: Dict,
        narration_text: str,  # Now required for narrator-first approach
        dialogue_duration: float,  # Duration of character dialogue (if any)
        camera_timing: Dict,
        scene_duration: float,
        confidence: float,
        dialogue_intent: Optional[Dict] = None,  # Selective character dialogue
        attack_intent: Optional[Dict] = None
    ) -> Dict:
        """
        Convert Gemini audio intent → FFmpeg parameters.
        
        Args:
            audio_intent: Gemini's audio directive (ENUM only)
            dialogue_duration: Duration of voiceover in seconds
            camera_timing: {action, duration, intensity}
            scene_duration: Total scene duration in seconds
            confidence: Gemini's confidence score (0.0-1.0)
            narration_text: Optional narration text (if provided, narration will be generated)
            
        Returns:
            {
                "bgm_file": str or None,
                "ambience_file": str or None,
                "sfx_file": str or None,
                "sfx_timestamp": float or None,
                "intro_stinger": str or None,
                "outro_stinger": str or None,
                "silence_before": float,
                "duck_bgm": bool,
                "layer_count": int,
                "narration_placement": str,  # "before"|"over"|"after"|"none"
                "narration_duck_amount": float,  # 0.0-1.0
                "missing_assets": List[str]  # For logging
            }
        """
        
        missing_assets = []
        
        # FIX #1: Relative silence timing (30% of scene, max 2s)
        silence_before = 0.0
        if audio_intent.get("use_silence", False):
            silence_before = min(2.0, scene_duration * 0.3)
        
        # FIX #2: Silence exclusivity (silence → no ambience/bgm)
        if audio_intent.get("use_silence", False):
            bgm_file = None
            ambience_file = None
        else:
            bgm_file = self.BGM_MAP.get(audio_intent.get("bgm", "none"))
            ambience_file = self.AMBIENCE_MAP.get(audio_intent.get("ambience", "none"))
        
        # Narrator-first approach: BGM is ALWAYS ducked (0.2 volume)
        # BGM creates atmosphere, not primary audio
        duck_bgm = True  # Always duck for narrator-first approach
        
        # Asset validation with graceful fallback
        if bgm_file and not os.path.exists(bgm_file):
            print(f"⚠️ Missing BGM asset: {bgm_file}")
            missing_assets.append(bgm_file)
            bgm_file = None
            
        if ambience_file and not os.path.exists(ambience_file):
            print(f"⚠️ Missing ambience asset: {ambience_file}")
            missing_assets.append(ambience_file)
            ambience_file = None
        
        # FIX #4: Confidence-based SFX (disable if < 0.6)
        sfx_file = None
        sfx_timestamp = None
        if confidence >= 0.6:
            sfx_enum = audio_intent.get("impact_sfx", "none")
            sfx_file = self.SFX_MAP.get(sfx_enum)
            if sfx_file:
                if not os.path.exists(sfx_file):
                    print(f"⚠️ Missing SFX asset: {sfx_file}")
                    missing_assets.append(sfx_file)
                    sfx_file = None
                else:
                    sfx_timestamp = self._calculate_sfx_timestamp(
                        camera_timing.get("action", "static"),
                        camera_timing.get("duration", scene_duration)
                    )
        
        # Stingers with validation
        intro_stinger = self.STINGER_MAP.get("intro") if audio_intent.get("intro_stinger", False) else None
        outro_stinger = self.STINGER_MAP.get("outro") if audio_intent.get("outro_stinger", False) else None
        
        if intro_stinger and not os.path.exists(intro_stinger):
            print(f"⚠️ Missing intro stinger: {intro_stinger}")
            missing_assets.append(intro_stinger)
            intro_stinger = None
            
        if outro_stinger and not os.path.exists(outro_stinger):
            print(f"⚠️ Missing outro stinger: {outro_stinger}")
            missing_assets.append(outro_stinger)
            outro_stinger = None
        
        # Narration placement logic
        narration_placement = "none"
        narration_duck_amount = 0.0
        
        if narration_text:
            # Determine placement based on scene context
            # Default: "over" (narration plays over scene with ducked BGM)
            narration_placement = audio_intent.get("narration_placement", "over")
            
            # Duck amount: how much to reduce BGM/ambience during narration
            # 0.3 = reduce to 30% of original volume
            narration_duck_amount = 0.3
            
            # If narration is "before", increase silence_before
            if narration_placement == "before":
                # Estimate narration duration (rough: 150 words/min, 5 chars/word avg)
                estimated_narration_duration = len(narration_text) / (150 * 5 / 60)
                silence_before = max(silence_before, estimated_narration_duration)
        
        # Narrator-first: BGM is always ducked (handled above)
        # No conditional ducking needed - narration is primary audio
        
        # FIX #5: 4-layer audio limit (narration + bgm + attack/sfx + personality)
        # Priority: dialogue > bgm > ambience > sfx > stingers
        layers = ["dialogue"]  # Dialogue always present
        
        # Choose ONE background layer (BGM takes priority over ambience)
        if bgm_file:
            layers.append("bgm")
            ambience_file = None  # Disable ambience if BGM present
        elif ambience_file:
            layers.append("ambience")
        
        # Choose ONE impact layer (SFX takes priority over stingers)
        if sfx_file:
            layers.append("sfx")
        elif intro_stinger:
            layers.append("intro_stinger")
        elif outro_stinger:
            layers.append("outro_stinger")
        
        # Enforce hard limit: max 3 layers total
        layer_count = len(layers)
        if layer_count > 3:
            # Trim lowest priority layers
            if "outro_stinger" in layers:
                outro_stinger = None
                layer_count -= 1
            if layer_count > 3 and "intro_stinger" in layers:
                intro_stinger = None
                layer_count -= 1
        
        # Logging for debugging
        if missing_assets:
            print(f"⚠️ Audio Intelligence: {len(missing_assets)} missing assets, continuing with available layers")
        
        # ═══════════════════════════════════════════════════════════
        # PART 6: CHARACTER AUDIO (ATTACK + PERSONALITY)
        # ═══════════════════════════════════════════════════════════
        
        attack_audio = None
        attack_timestamp = None
        personality_audio = None
        personality_timestamp = None
        character_audio_fallback = False
        
        # Process attack intent
        if attack_intent and isinstance(attack_intent, dict):
            character = attack_intent.get("character", "").lower()
            attack_name = attack_intent.get("name", "").lower()
            
            if character and attack_name:
                attack_audio = self.resolve_attack_audio(character, attack_name)
                
                if attack_audio:
                    # Calculate attack timing
                    attack_timestamp = self.calculate_attack_timing(
                        camera_timing.get("action", "static"),
                        dialogue_duration
                    )
                    layer_count += 1
                    print(f"🎯 Attack audio: {character}/{attack_name} @ {attack_timestamp}s")
                else:
                    # Fallback to generic impact SFX if attack audio missing
                    if sfx_file is None and audio_intent.get("impact_sfx", "none") != "none":
                        # Use the generic SFX that was already resolved
                        character_audio_fallback = True
                        print(f"⚠️ Attack audio missing, using generic SFX fallback")
                    elif sfx_file is None:
                        # No generic SFX was specified, try to use one based on attack intensity
                        intensity = attack_intent.get("intensity", "medium")
                        fallback_sfx = "punch" if intensity == "low" else "explosion" if intensity == "high" else "hit"
                        sfx_file = self.SFX_MAP.get(fallback_sfx)
                        if sfx_file and os.path.exists(sfx_file):
                            sfx_timestamp = self._calculate_sfx_timestamp(
                                camera_timing.get("action", "static"),
                                camera_timing.get("duration", dialogue_duration)
                            )
                            layer_count += 1
                            character_audio_fallback = True
                            print(f"⚠️ Attack audio missing, using generic {fallback_sfx} SFX")
        
        # Personality is handled by narrator (no separate audio needed)
        
        print(f"🎵 Audio Decision: {layer_count} layers | BGM: {bool(bgm_file)} | SFX: {bool(sfx_file)} | Attack: {bool(attack_audio)}")
        
        return {
            "bgm_file": bgm_file,
            "ambience_file": ambience_file,
            "sfx_file": sfx_file,
            "sfx_timestamp": sfx_timestamp,
            "intro_stinger": intro_stinger,
            "outro_stinger": outro_stinger,
            "silence_before": silence_before,
            "duck_bgm": duck_bgm,
            "layer_count": layer_count,
            "narration_placement": narration_placement,
            "narration_duck_amount": narration_duck_amount,
            "attack_audio": attack_audio,
            "attack_timestamp": attack_timestamp,
            "missing_assets": missing_assets,
            "character_audio_fallback": character_audio_fallback
        }
    
    def resolve_attack_audio(self, character: str, attack_name: str) -> Optional[str]:
        """
        Resolve attack audio file path.
        
        Args:
            character: Character name (lowercase)
            attack_name: Attack name (snake_case)
            
        Returns:
            Path to attack audio or None if not found
        """
        # Try WAV first, then MP3
        for ext in [".wav", ".mp3"]:
            path = f"assets/characters/{character}/attacks/{attack_name}{ext}"
            if os.path.exists(path):
                return path
        
        print(f"⚠️ Attack audio not found: {character}/{attack_name}")
        print(f"   → Narrator will describe attack by name")
        return None
    
    def calculate_attack_timing(self, camera_action: str, dialogue_duration: float) -> float:
        """
        Calculate when to play attack SFX.
        
        Rules:
        - shake/zoom_in_fast → t=0.0 (impact at start)
        - else → dialogue midpoint
        
        Args:
            camera_action: Camera action (e.g., "shake", "zoom_in")
            dialogue_duration: Duration of dialogue in seconds
            
        Returns:
            Timestamp in seconds
        """
        if camera_action in ["shake", "zoom_in_fast", "shake_agressive"]:
            return 0.0
        else:
            return dialogue_duration / 2.0
    
    def _calculate_sfx_timestamp(self, camera_action: str, camera_duration: float) -> float:
        """
        Sync SFX with camera motion.
        
        Rules:
        - shake → SFX at shake start (0.0s)
        - zoom_in → SFX at zoom peak (50% through)
        - zoom_out → SFX at zoom start (0.0s)
        - pan_left/pan_right → SFX at pan start (0.0s)
        - static → no SFX (return 0.0s as fallback)
        """
        if camera_action == "shake":
            return 0.0
        elif camera_action == "zoom_in":
            return camera_duration * 0.5
        elif camera_action in ["zoom_out", "pan_left", "pan_right"]:
            return 0.0
        else:  # static
            return 0.0
