# intelligence/comic_brain.py - Professional Manga Animation Director AI
import os
import json
import google.generativeai as genai
from typing import Dict, Optional, List
from config.config import GEMINI_API_KEY, GEMINI_MODEL

class ComicBrain:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment.")
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.character_memory = {}  # Persistent character knowledge
        self.previous_scene_summary = None  # Continuity tracking
        
    def analyze_scene(self, image_path: str, ocr_text: str, scene_index: int = 0) -> Dict:
        """
        Professional manga director analysis with character memory and continuity.
        Optimized for minimal API calls and maximum narrative value.
        """
        
        # Build character memory context
        known_chars_str = json.dumps(self.character_memory) if self.character_memory else "{}"
        prev_summary = self.previous_scene_summary or "First scene of chapter"
        
        prompt = f"""You are a PROFESSIONAL MANGA ANIMATION DIRECTOR AI.

Your job is to analyze manga panels and produce STRUCTURED, DETERMINISTIC animation instructions.

This system is optimized for MINIMAL API CALLS. Every response must maximize narrative value.

═══════════════════════════════════════════════════════════════
GLOBAL CONTEXT (PERSISTENT)
═══════════════════════════════════════════════════════════════

Scene #{scene_index + 1}
Previous Scene: {prev_summary}

KNOWN_CHARACTERS (DO NOT RE-IDENTIFY):
{known_chars_str}

OCR Text Extracted:
{ocr_text}

═══════════════════════════════════════════════════════════════
CHARACTER MEMORY RULES (CRITICAL)
═══════════════════════════════════════════════════════════════

- If a character is in KNOWN_CHARACTERS, use them directly
- NEVER re-describe appearance for known characters
- ONLY infer emotion and dialogue
- If a NEW character appears, name them ONCE and mark is_new=true

═══════════════════════════════════════════════════════════════
SCENE ANALYSIS RULES
═══════════════════════════════════════════════════════════════

Focus on:
1. Dialogue flow
2. Emotional state
3. Narrative intent
4. Camera suggestion

IGNORE:
- Background-only panels
- Silent transitions
- Redundant reactions

If scene has no dialogue and no emotion change → Mark is_silent=true

═══════════════════════════════════════════════════════════════
OUTPUT SCHEMA (STRICT – NO DEVIATION)
═══════════════════════════════════════════════════════════════

Respond ONLY with valid JSON:

{{
  "scene_summary": "one sentence for continuity",
  "confidence": 0.0-1.0,
  "is_silent": true|false,
  "narration": "2-4 sentences describing the scene cinematically, like a documentary narrator. Focus on action, emotion, and atmosphere. This is the PRIMARY audio.",
  "characters": [
    {{
      "name": "string",
      "is_new": true|false,
      "emotion": "neutral|anger|joy|sadness|surprise|fear"
    }}
  ],
  "character_dialogue": {{
    "character": "string (lowercase)",
    "line": "string (< 5 words, iconic moments ONLY)",
    "timing": "scene_start|mid_scene|scene_end",
    "is_iconic": true|false
  }},
  "camera": {{
    "action": "static|pan_left|pan_right|zoom_in|zoom_out|shake",
    "intensity": "low|medium|high"
  }},
  "audio": {{
    "bgm": "none|calm|tense|heroic|sad",
    "ambience": "none|wind|sea|crowd|room",
    "impact_sfx": "none|punch|slash|explosion|hit",
    "use_silence": true|false,
    "duck_bgm": true,
    "intro_stinger": true|false,
    "outro_stinger": true|false
  }},
  "attack": {{
    "character": "string (lowercase)",
    "name": "string (snake_case)",
    "intensity": "low|medium|high"
  }}
}}

NARRATION RULES (CRITICAL - PRIMARY AUDIO):
- narration: ALWAYS output 2-4 sentences describing the scene
  - Write like a professional documentary narrator
  - Describe action, emotion, atmosphere, and context
  - Use cinematic language (e.g., "charges forward", "gazes at the horizon")
  - **INCLUDE ATTACK NAMES when attacks are used** (e.g., "Luffy unleashes his Gum Gum Pistol")
  - This is the MAIN storytelling layer
  - Example: "Luffy charges forward, his fist glowing with Haki. With a thunderous roar, he unleashes his Gum Gum Pistol, striking with devastating force."

CHARACTER DIALOGUE RULES (SELECTIVE - 20% OF SCENES):
- character_dialogue: OPTIONAL - only for iconic moments
  - line: < 5 words (catchphrases, attack names, reactions)
  - Examples: "GUM GUM PISTOL!", "I'll be the Pirate King!", "SUPER!"
  - timing: When to play (scene_start, mid_scene, scene_end)
  - is_iconic: true if this is a signature character moment
  - If no iconic dialogue → OMIT this block entirely
  - DO NOT output regular conversation - use narration for that

AUDIO INTENT RULES (ATMOSPHERIC - ALWAYS PRESENT):
- bgm: Background music mood (ALWAYS set, creates atmosphere)
  - Ducked to 0.2 volume under narration
  - Matches scene emotion (calm, tense, heroic, sad)
- ambience: Environmental sound (wind, sea, crowd, room)
  - Creates immersion and location feel
- impact_sfx: Action sound effect (punch, slash, explosion, hit)
  - Timed to camera action
- use_silence: Brief silence before scene for dramatic effect
- duck_bgm: ALWAYS true (BGM is ducked under narration)
- intro_stinger/outro_stinger: Musical punctuation for transitions

CHARACTER AUDIO RULES (OPTIONAL):
- attack: ONLY output if a NAMED attack is clearly used
  - character: Character performing attack (lowercase)
  - name: Canonical attack name (snake_case)
  - intensity: Attack power level
  - **IMPORTANT:** Attack name MUST be mentioned in narration text
  - If attack audio exists → play it; if not → narration describes it
  - If unsure → OMIT attack block entirely

CRITICAL:
- Narration is PRIMARY - always output rich, cinematic description
- **Attack names MUST appear in narration** (narrator describes them)
- Character dialogue is SELECTIVE - only iconic moments (< 5 words)
- BGM/SFX are ATMOSPHERIC - create mood, ducked under narration
- Output INTENT only, NO filenames or timing values
- If unsure → choose "none" or omit optional blocks
- Match audio to scene emotion and camera action
- If use_silence=true → bgm and ambience should be "none"

Rules:
- If is_silent=true → characters may be empty
- Dialogue must be concise (spoken text only)
- Camera action must match emotional intensity
- No free text outside JSON

═══════════════════════════════════════════════════════════════
REQUEST EFFICIENCY RULES
═══════════════════════════════════════════════════════════════

You are part of a COST-AWARE system.

- Combine reasoning across panels
- Prefer continuity over repetition
- Avoid over-analysis
- Use defaults when uncertain

If confidence < 0.5:
- Choose conservative emotion (neutral)
- Choose static or slow camera

═══════════════════════════════════════════════════════════════
FAILURE SAFETY
═══════════════════════════════════════════════════════════════

If input is unclear:
- Do NOT hallucinate
- Mark confidence low
- Use neutral emotion
- Use static camera

═══════════════════════════════════════════════════════════════
REMEMBER
═══════════════════════════════════════════════════════════════

You are not writing prose.
You are issuing DIRECTOR INSTRUCTIONS for an animation engine.

Be precise. Be minimal. Be consistent.
Same input → Same output.
"""
        
        try:
            # Upload image to Gemini
            sample_file = genai.upload_file(path=image_path, display_name=f"Scene_{scene_index}")
            
            response = self.model.generate_content([prompt, sample_file])
            
            # Clean response text
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                
            result = json.loads(text)
            
            # Update character memory with new characters
            for char in result.get("characters", []):
                if char.get("is_new") and char["name"] not in self.character_memory:
                    self.character_memory[char["name"]] = {
                        "first_seen": scene_index,
                        "baseline": char.get("emotion", "neutral")
                    }
            
            # Update continuity
            self.previous_scene_summary = result.get("scene_summary", "")
            
            # Legacy compatibility: map to old format
            legacy_result = {
                "character_name": result["characters"][0]["name"] if result.get("characters") else "unknown",
                "emotion": result["characters"][0]["emotion"].upper() if result.get("characters") else "NEUTRAL",
                "camera_action": result["camera"]["action"].upper(),
                "voiceover_script": result["characters"][0].get("dialogue", "The scene continues.") if result.get("characters") else "The scene continues.",
                "confidence_score": result.get("confidence", 0.5),
                "_raw_director_output": result  # Store full output for future use
            }
            
            return legacy_result
            
        except Exception as e:
            print(f"⚠️ Gemini Error: {e}")
            return {
                "character_name": "unknown",
                "emotion": "NEUTRAL",
                "camera_action": "STATIC",
                "voiceover_script": "The scene continues with quiet intensity.",
                "confidence_score": 0.0,
                "_raw_director_output": None
            }
    
    def reset_memory(self):
        """Reset character memory for new chapter."""
        self.character_memory = {}
        self.previous_scene_summary = None
