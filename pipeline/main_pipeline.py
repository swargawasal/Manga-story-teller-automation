# main_pipeline.py - Comic/Manga Automation Orchestrator (INFRASTRUCTURE AWARE)
import os
import subprocess
from infra import gpu_utils
from config.config import TEMP_DIR, OUTPUT_DIR
from input.downloader import process_manga_input
from processing.panel_detector import PanelDetector
from processing.scene_grouper import SceneGrouper
from processing.ocr_engine import OCREngine
from intelligence.comic_brain import ComicBrain
from audio.voice_memory import VoiceMemory
from audio.tts_engine import TTSEngine
from video.animation_engine import generate_animation_command
from processing.pdf_processor import process_pdf

class ComicAutomationPipeline:
    def __init__(self):
        self.detector = PanelDetector()
        self.grouper = SceneGrouper()
        self.ocr = OCREngine()
        self.brain = ComicBrain()
        self.voice_memory = VoiceMemory()
        self.tts = TTSEngine()

    def run_pipeline(self, input_path: str, output_filename: str = "final_output.mp4"):
        print(f"🎬 Starting Comic Automation Pipeline: {input_path}")
        
        # 0. GPU Awareness
        gpu_status = gpu_utils.get_gpu_status()
        if gpu_status["available"]:
            print(f"🎮 GPU Detected: {gpu_status['device']} ({gpu_status['free_mb']}MB Free)")
        
        # 1. Input Processing
        page_paths = process_manga_input(input_path)
        if not page_paths:
            print("❌ No pages found to process.")
            return

        # 2. Page & Panel Processing (with GPU Guard)
        all_panels = []
        for i, page_path in enumerate(page_paths):
            print(f"🔍 Detecting panels on page {i+1}/{len(page_paths)}...")
            panels = gpu_utils.run_with_gpu_guard(
                self.detector.extract_and_save_panels, 
                page_path, 
                f"page_{i}"
            )
            all_panels.extend(panels)
            
        # 3. Grouping
        scenes = self.grouper.group_panels(all_panels)
        print(f"📦 Grouped {len(all_panels)} panels into {len(scenes)} scenes.")
        
        # Initialize audio intelligence
        from audio.audio_intelligence import AudioIntelligence
        from video.animation_engine import get_camera_timing
        from video.composer import mix_scene_audio
        audio_intelligence = AudioIntelligence()
        
        scene_clips = []
        for i, scene in enumerate(scenes):
            print(f"🎥 Processing Scene {i+1}/{len(scenes)}...")
            
            # 4. OCR (GPU Guarded)
            scene_text = ""
            for panel_path in scene:
                text = gpu_utils.run_with_gpu_guard(self.ocr.get_full_text, panel_path)
                scene_text += text + " "
            
            # 5. Reasoning (with continuity tracking)
            ref_panel = scene[len(scene)//2]
            scene_analysis = self.brain.analyze_scene(ref_panel, scene_text, scene_index=i)
            
            # 6. Audio - Generate dialogue voiceover
            voice = self.voice_memory.get_voice(scene_analysis['character_name'])
            audio_path = self.tts.generate_voiceover(
                scene_analysis['voiceover_script'],
                voice,
                f"scene_{i}_audio.mp3"
            )
            
            # Get audio duration for timing calculations
            from video.animation_engine import get_audio_duration
            audio_duration = get_audio_duration(audio_path)
            
            # 7. Animation (FFmpeg) - Create base video clip
            clip_path = os.path.join(TEMP_DIR, f"scene_{i}_clip.mp4")
            anim_cmd = generate_animation_command(
                ref_panel,
                audio_path,
                clip_path,
                emotion=scene_analysis['emotion']
            )
            
            print(f"📽️ Animating scene {i+1}...")
            subprocess.run(anim_cmd, check=True)
            
            
            # 8. Auto-create character folders for new characters
            from utils.character_manager import CharacterAssetManager
            char_manager = CharacterAssetManager()
            
            raw_output = scene_analysis.get("_raw_director_output", {})
            characters = raw_output.get("characters", [])
            for char in characters:
                if char.get("is_new"):
                    char_manager.ensure_character_folders(char.get("name", ""))
            
            # 9. Extract narration (PRIMARY AUDIO)
            narration_text = raw_output.get("narration", "")
            
            # 10. Extract character dialogue (SELECTIVE - iconic moments only)
            dialogue_intent = raw_output.get("character_dialogue", {})
            
            # 11. Audio Intelligence - Process audio intent
            audio_intent = raw_output.get("audio", {})
            attack_intent = raw_output.get("attack", {})
            personality_intent = raw_output.get("personality_cue", {})
            
            # Get camera timing for SFX synchronization
            camera_timing = get_camera_timing(
                scene_analysis['emotion'],
                audio_duration
            )
            
            # Process audio intent to get mixing parameters (narrator-first)
            audio_params = audio_intelligence.process_audio_intent(
                audio_intent=audio_intent,
                narration_text=narration_text,  # Required for narrator-first
                dialogue_duration=audio_duration,
                camera_timing=camera_timing,
                scene_duration=audio_duration,
                confidence=scene_analysis['confidence_score'],
                dialogue_intent=dialogue_intent,  # Selective character dialogue
                attack_intent=attack_intent
            )
            
            # 9. Audio Mixing - Mix all audio layers
            final_clip_path = os.path.join(TEMP_DIR, f"scene_{i}_final.mp4")
            mixed_clip = mix_scene_audio(
                video_path=clip_path,
                dialogue_path=audio_path,
                audio_params=audio_params,
                output_path=final_clip_path
            )
            
            scene_clips.append(mixed_clip)
            
            # Periodically clear GPU cache to prevent fragmentation
            if i % 5 == 0:
                gpu_utils.clear_gpu_cache()
            
        # 10. Composition
        from video.composer import concatenate_clips, finalize_video
        final_video = finalize_video(concatenate_clips(scene_clips, output_filename), output_filename)
        print(f"✅ Pipeline COMPLETED! Final Video: {final_video}")
        return final_video
