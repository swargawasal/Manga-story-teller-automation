"""
Offline Audio Asset Factory (STUDIO TOOL - NOT RUNTIME)

CRITICAL: This is an OFFLINE-ONLY tool for one-time asset generation.
DO NOT use in runtime pipeline - destroys determinism.

Usage:
    python scripts/generate_audio_library.py  # Run once
    
Runtime pipeline uses assets/ only (deterministic selection).
"""
import os
import torch
import numpy as np
import soundfile as sf
from typing import Optional, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class AudioAssetGenerator:
    """Fully automated audio generation with AI curation."""
    
    def __init__(self):
        """Initialize AI models (lazy loading)."""
        self._music_model = None
        self._sfx_model = None
        
        # Prompts for each asset type
        self.BGM_PROMPTS = {
            "calm": "peaceful ambient music, soft piano, slow tempo 60 bpm, emotional calm scene",
            "tense": "dark suspenseful orchestral music, 120 bpm, minor key, thriller atmosphere",
            "heroic": "epic orchestral music, triumphant brass horns, fast tempo 140 bpm, cinematic action",
            "sad": "melancholic piano music, slow strings, emotional, minor key, sorrowful"
        }
        
        self.SFX_PROMPTS = {
            "punch": "heavy punch impact sound, deep thud, powerful hit",
            "slash": "sword slash cutting air, sharp whoosh, blade swing",
            "explosion": "large explosion sound, deep bass boom, dramatic blast",
            "hit": "impact hit sound, crack, sharp strike"
        }
        
        self.AMBIENCE_PROMPTS = {
            "wind": "strong wind blowing, outdoor atmosphere, natural wind sound",
            "sea": "ocean waves crashing, seagulls in distance, beach ambience",
            "crowd": "large crowd murmuring, background chatter, people talking",
            "room": "quiet room tone, subtle air conditioning hum, indoor ambience"
        }
        
        self.STINGER_PROMPTS = {
            "intro": "dramatic orchestral stinger, 2 seconds, rising tension, scene intro",
            "outro": "suspenseful cliffhanger music sting, 3 seconds, dramatic ending"
        }
    
    @property
    def music_model(self):
        """Lazy load MusicGen-medium with optimizations."""
        if self._music_model is None:
            print("🎵 Loading MusicGen-medium (optimized for T4 GPU)...")
            from audiocraft.models import MusicGen
            
            # Load medium model (9/10 quality vs 8/10 for small)
            self._music_model = MusicGen.get_pretrained('facebook/musicgen-medium')
            
            # Apply optimizations (offline only)
            print("  ⚡ Applying FP16 + torch.compile optimizations...")
            self._music_model = self._music_model.half()  # FP16 (2× faster)
            
            try:
                import torch
                self._music_model = torch.compile(self._music_model, mode="reduce-overhead")  # 20-30% faster
                print("  ✅ Optimizations applied")
            except Exception as e:
                print(f"  ⚠️ torch.compile failed (using FP16 only): {e}")
        
        return self._music_model
    
    @property
    def sfx_model(self):
        """Lazy load AudioLDM 2 with optimizations."""
        if self._sfx_model is None:
            print("🔊 Loading AudioLDM 2 (optimized for T4 GPU)...")
            try:
                from audioldm2 import text_to_audio, build_model
                self._sfx_model = build_model()
                
                # Apply optimizations (offline only)
                print("  ⚡ Applying FP16 optimization...")
                self._sfx_model = self._sfx_model.half()  # FP16
                
                try:
                    import torch
                    self._sfx_model = torch.compile(self._sfx_model, mode="reduce-overhead")
                    print("  ✅ Optimizations applied")
                except Exception as e:
                    print(f"  ⚠️ torch.compile failed (using FP16 only): {e}")
                    
            except ImportError:
                print("⚠️ AudioLDM 2 not installed. Using MusicGen for SFX.")
                self._sfx_model = self.music_model
        return self._sfx_model
    
    def auto_score_bgm(self, audio_path: str, target_mood: str) -> float:
        """
        Automatically score BGM quality using audio analysis.
        NO HUMAN INPUT REQUIRED.
        
        Args:
            audio_path: Path to audio file
            target_mood: Target mood (calm, tense, heroic, sad)
            
        Returns:
            Quality score (0.0-1.0)
        """
        try:
            import librosa
        except ImportError:
            print("⚠️ librosa not installed. Using random scoring.")
            return np.random.random()
        
        y, sr = librosa.load(audio_path, duration=10)  # Analyze first 10s
        
        # 1. Energy (RMS)
        rms = librosa.feature.rms(y=y)[0].mean()
        
        # 2. Tempo (BPM)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # 3. Brightness (Spectral Centroid)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean()
        
        # 4. Dynamic Range
        dynamic_range = np.max(y) - np.min(y)
        
        # 5. Harmonic Content
        harmonic, percussive = librosa.effects.hpss(y)
        harmonic_ratio = np.mean(np.abs(harmonic)) / (np.mean(np.abs(y)) + 1e-6)
        
        # Score based on target mood
        if target_mood == "heroic":
            # High energy, fast tempo, bright, dynamic
            score = (
                (rms * 2.0) +
                (min(tempo / 140, 1.0) * 2.0) +
                (spectral_centroid / 5000 * 1.5) +
                (dynamic_range * 1.5)
            )
        elif target_mood == "tense":
            # Medium energy, medium tempo, dark, very dynamic
            score = (
                (rms * 1.5) +
                (min(tempo / 120, 1.0) * 1.5) +
                ((1 - spectral_centroid / 5000) * 2.0) +
                (dynamic_range * 2.5)
            )
        elif target_mood == "calm":
            # Low energy, slow tempo, soft, smooth
            score = (
                ((1 - rms) * 2.0) +
                ((1 - min(tempo / 140, 1.0)) * 2.0) +
                (harmonic_ratio * 2.0) +
                ((1 - dynamic_range) * 1.5)
            )
        elif target_mood == "sad":
            # Low energy, slow tempo, dark, harmonic
            score = (
                ((1 - rms) * 2.0) +
                ((1 - min(tempo / 140, 1.0)) * 2.0) +
                ((1 - spectral_centroid / 5000) * 1.5) +
                (harmonic_ratio * 2.0)
            )
        else:
            score = 5.0
        
        return min(score / 10.0, 1.0)  # Normalize to 0-1
    
    def normalize_loudness(self, audio_path: str, target_lufs: float = -14.0) -> str:
        """
        Normalize audio to YouTube-safe loudness.
        
        Args:
            audio_path: Path to audio file
            target_lufs: Target LUFS (default: -14 for YouTube)
            
        Returns:
            Path to normalized audio
        """
        try:
            import pyloudnorm as pyln
        except ImportError:
            print("⚠️ pyloudnorm not installed. Skipping normalization.")
            return audio_path
        
        # Load audio
        y, sr = sf.read(audio_path)
        
        # Measure loudness
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(y)
        
        # Normalize
        y_normalized = pyln.normalize.loudness(y, loudness, target_lufs)
        
        # Save
        sf.write(audio_path, y_normalized, sr)
        
        return audio_path
    
    def generate_bgm(self, mood: str, duration: int = 30, num_variations: int = 5) -> str:
        """
        Generate BGM with auto-curation.
        
        Args:
            mood: BGM mood (calm, tense, heroic, sad)
            duration: Duration in seconds
            num_variations: Number of variations to generate
            
        Returns:
            Path to best BGM file
        """
        output_path = f"assets/bgm/{mood}_loop.wav"
        
        # Skip if file exists
        if os.path.exists(output_path):
            print(f"✅ Using existing BGM: {mood}_loop.wav")
            return output_path
        
        os.makedirs("assets/bgm", exist_ok=True)
        
        prompt = self.BGM_PROMPTS.get(mood, "ambient background music")
        
        print(f"🎵 Generating {mood} BGM ({num_variations} variations)...")
        
        # Generate variations
        descriptions = [prompt] * num_variations
        wav_batch = self.music_model.generate(descriptions, progress=True)
        
        # Auto-curate: score each variation
        best_score = 0
        best_wav = None
        
        for i, wav in enumerate(wav_batch):
            # Save temp file for analysis
            temp_path = f"temp_{mood}_{i}.wav"
            sf.write(temp_path, wav.cpu().numpy().T, self.music_model.sample_rate)
            
            # Score quality
            score = self.auto_score_bgm(temp_path, mood)
            print(f"  Variation {i+1}: score {score:.2f}")
            
            if score > best_score:
                best_score = score
                best_wav = wav
            
            # Cleanup temp file
            os.remove(temp_path)
        
        # Save best variation
        print(f"  ✅ Best variation: score {best_score:.2f}")
        sf.write(output_path, best_wav.cpu().numpy().T, self.music_model.sample_rate)
        
        # Normalize loudness
        print(f"  🔊 Normalizing to -14 LUFS...")
        self.normalize_loudness(output_path)
        
        print(f"  💾 Saved: {output_path}")
        
        return output_path
    
    def generate_sfx(self, sfx_type: str, duration: float = 1.0) -> str:
        """
        Generate SFX.
        
        Args:
            sfx_type: SFX type (punch, slash, explosion, hit)
            duration: Duration in seconds
            
        Returns:
            Path to SFX file
        """
        output_path = f"assets/sfx/{sfx_type}.wav"
        
        # Skip if file exists
        if os.path.exists(output_path):
            print(f"✅ Using existing SFX: {sfx_type}.wav")
            return output_path
        
        os.makedirs("assets/sfx", exist_ok=True)
        
        prompt = self.SFX_PROMPTS.get(sfx_type, "impact sound effect")
        
        print(f"🔊 Generating {sfx_type} SFX...")
        
        try:
            # Try AudioLDM 2 with optimized inference steps
            from audioldm2 import text_to_audio
            audio = text_to_audio(
                prompt,
                duration=duration,
                num_inference_steps=30,  # Reduced from 50 (minimal quality loss, 2× faster)
                model=self.sfx_model
            )
            sf.write(output_path, audio, 16000)
        except:
            # Fallback to MusicGen
            wav = self.music_model.generate([prompt], duration=duration)
            sf.write(output_path, wav[0].cpu().numpy().T, self.music_model.sample_rate)
        
        print(f"  💾 Saved: {output_path}")
        
        return output_path
    
    def generate_ambience(self, ambience_type: str, duration: int = 30) -> str:
        """
        Generate ambience.
        
        Args:
            ambience_type: Ambience type (wind, sea, crowd, room)
            duration: Duration in seconds
            
        Returns:
            Path to ambience file
        """
        output_path = f"assets/ambience/{ambience_type}.wav"
        
        # Skip if file exists
        if os.path.exists(output_path):
            print(f"✅ Using existing ambience: {ambience_type}.wav")
            return output_path
        
        os.makedirs("assets/ambience", exist_ok=True)
        
        prompt = self.AMBIENCE_PROMPTS.get(ambience_type, "ambient background sound")
        
        print(f"🌊 Generating {ambience_type} ambience...")
        
        try:
            # Try AudioLDM 2 with optimized inference steps
            from audioldm2 import text_to_audio
            audio = text_to_audio(
                prompt,
                duration=duration,
                num_inference_steps=30,  # Reduced from 50 (minimal quality loss, 2× faster)
                model=self.sfx_model
            )
            sf.write(output_path, audio, 16000)
        except:
            # Fallback to MusicGen
            wav = self.music_model.generate([prompt], duration=duration)
            sf.write(output_path, wav[0].cpu().numpy().T, self.music_model.sample_rate)
        
        print(f"  💾 Saved: {output_path}")
        
        return output_path
    
    def generate_stinger(self, stinger_type: str, duration: int = 2) -> str:
        """
        Generate stinger.
        
        Args:
            stinger_type: Stinger type (intro, outro)
            duration: Duration in seconds
            
        Returns:
            Path to stinger file
        """
        output_path = f"assets/stingers/{stinger_type}.wav"
        
        # Skip if file exists
        if os.path.exists(output_path):
            print(f"✅ Using existing stinger: {stinger_type}.wav")
            return output_path
        
        os.makedirs("assets/stingers", exist_ok=True)
        
        prompt = self.STINGER_PROMPTS.get(stinger_type, "dramatic music stinger")
        
        print(f"🎺 Generating {stinger_type} stinger...")
        
        wav = self.music_model.generate([prompt], duration=duration)
        sf.write(output_path, wav[0].cpu().numpy().T, self.music_model.sample_rate)
        
        print(f"  💾 Saved: {output_path}")
        
        return output_path
