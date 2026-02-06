#!/usr/bin/env python3
"""
Audio Asset Library Generator
One-time setup script to generate all BGM, SFX, ambience, and stingers.
Fully automated with AI curation.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.audio_generator import AudioAssetGenerator

def generate_all_assets():
    """Generate complete audio library."""
    print("=" * 60)
    print("AUDIO ASSET LIBRARY GENERATOR")
    print("=" * 60)
    print("\n🤖 Fully automated with AI curation")
    print("⏱️  This will take 10-20 minutes on GPU")
    print("💡 Files will be skipped if they already exist\n")
    
    generator = AudioAssetGenerator()
    
    # Generate BGM
    print("\n" + "=" * 60)
    print("🎵 GENERATING BGM LIBRARY")
    print("=" * 60)
    
    bgm_moods = ["calm", "tense", "heroic", "sad"]
    for mood in bgm_moods:
        generator.generate_bgm(mood, duration=30, num_variations=5)
    
    # Generate SFX
    print("\n" + "=" * 60)
    print("🔊 GENERATING SFX LIBRARY")
    print("=" * 60)
    
    sfx_types = ["punch", "slash", "explosion", "hit"]
    for sfx_type in sfx_types:
        generator.generate_sfx(sfx_type, duration=1.0)
    
    # Generate Ambience
    print("\n" + "=" * 60)
    print("🌊 GENERATING AMBIENCE LIBRARY")
    print("=" * 60)
    
    ambience_types = ["wind", "sea", "crowd", "room"]
    for ambience_type in ambience_types:
        generator.generate_ambience(ambience_type, duration=30)
    
    # Generate Stingers
    print("\n" + "=" * 60)
    print("🎺 GENERATING STINGERS")
    print("=" * 60)
    
    generator.generate_stinger("intro", duration=2)
    generator.generate_stinger("outro", duration=3)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ AUDIO LIBRARY GENERATION COMPLETE!")
    print("=" * 60)
    
    total_files = len(bgm_moods) + len(sfx_types) + len(ambience_types) + 2
    print(f"\n📊 Generated {total_files} audio files:")
    print(f"  - {len(bgm_moods)} BGM loops")
    print(f"  - {len(sfx_types)} SFX")
    print(f"  - {len(ambience_types)} ambience tracks")
    print(f"  - 2 stingers")
    
    print("\n💡 To replace any file with your own:")
    print("   1. Delete the auto-generated file")
    print("   2. Add your own file with the same name")
    print("   3. Bot will use your version instead")
    
    print("\n🎬 Your bot is ready for cinematic storytelling!")

if __name__ == "__main__":
    generate_all_assets()
