# composer.py - Professional FFmpeg Audio/Video Composer
import subprocess
import os
from typing import List, Dict, Optional
from config.config import OUTPUT_DIR, TEMP_DIR

def concatenate_clips(clip_paths: List[str], output_filename: str) -> str:
    """
    Concatenates a list of MP4 clips into a single final video.
    """
    list_path = os.path.join(TEMP_DIR, "clips_list.txt")
    with open(list_path, 'w') as f:
        for clip in clip_paths:
            f.write(f"file '{os.path.abspath(clip).replace(os.sep, '/')}'\n")
            
    raw_output = os.path.join(TEMP_DIR, f"raw_{output_filename}")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        raw_output
    ]
    
    print(f"🎬 Concatenating {len(clip_paths)} clips...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return raw_output


def mix_scene_audio(
    video_path: str,
    dialogue_path: str,
    audio_params: Dict,
    output_path: str,
    narration_path: Optional[str] = None
) -> str:
    """
    Professional audio mixing with FFmpeg.
    Implements all audio intelligence directives with 3-layer limit.
    
    Args:
        video_path: Path to video clip (may have no audio)
        dialogue_path: Path to voiceover audio
        audio_params: Output from AudioIntelligence.process_audio_intent()
        output_path: Final output path
        narration_path: Optional path to narration audio
        
    Returns:
        Path to final mixed video
    """
    
    # Extract parameters
    bgm_file = audio_params.get("bgm_file")
    ambience_file = audio_params.get("ambience_file")
    sfx_file = audio_params.get("sfx_file")
    sfx_timestamp = audio_params.get("sfx_timestamp", 0.0)
    intro_stinger = audio_params.get("intro_stinger")
    outro_stinger = audio_params.get("outro_stinger")
    silence_before = audio_params.get("silence_before", 0.0)
    duck_bgm = audio_params.get("duck_bgm", False)
    layer_count = audio_params.get("layer_count", 1)
    narration_placement = audio_params.get("narration_placement", "none")
    narration_duck_amount = audio_params.get("narration_duck_amount", 0.3)
    attack_audio = audio_params.get("attack_audio")
    attack_timestamp = audio_params.get("attack_timestamp", 0.0)
    personality_audio = audio_params.get("personality_audio")
    personality_timestamp = audio_params.get("personality_timestamp", 0.0)
    
    print(f"🎵 Mixing audio: {layer_count} layers (dialogue + {layer_count-1} others)")
    
    # Get video duration
    duration_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
    scene_duration = float(duration_result.stdout.strip())
    
    # Build FFmpeg command
    inputs = ["-i", video_path]
    filter_parts = []
    audio_inputs = []
    input_index = 1  # Track input index (0 is video)
    
    # Add silence before scene if requested
    if silence_before > 0:
        print(f"🔇 Adding {silence_before:.2f}s silence before scene")
        filter_parts.append(
            f"anullsrc=r=44100:cl=stereo:d={silence_before}[silence]"
        )
    
    # Add dialogue
    inputs.extend(["-i", dialogue_path])
    dialogue_index = input_index
    input_index += 1
    
    # Handle narration placement
    if narration_path and narration_placement != "none":
        inputs.extend(["-i", narration_path])
        narration_index = input_index
        input_index += 1
        
        if narration_placement == "before":
            # Concatenate narration before dialogue
            filter_parts.append(
                f"[{narration_index}:a][{dialogue_index}:a]concat=n=2:v=0:a=1[dialogue_with_narration]"
            )
            audio_inputs.append("dialogue_with_narration")
        elif narration_placement == "over":
            # Mix narration over dialogue (narration louder)
            filter_parts.append(
                f"[{narration_index}:a]volume=1.0[narration_vol];"
                f"[{dialogue_index}:a]volume=0.6[dialogue_ducked];"
                f"[narration_vol][dialogue_ducked]amix=inputs=2:duration=longest[dialogue_with_narration]"
            )
            audio_inputs.append("dialogue_with_narration")
        elif narration_placement == "after":
            # Concatenate dialogue before narration
            filter_parts.append(
                f"[{dialogue_index}:a][{narration_index}:a]concat=n=2:v=0:a=1[dialogue_with_narration]"
            )
            audio_inputs.append("dialogue_with_narration")
    else:
        # No narration, just use dialogue
        audio_inputs.append(f"{dialogue_index}:a")
    
    # Add BGM (looped to scene duration with seamless crossfade)
    if bgm_file and os.path.exists(bgm_file):
        inputs.extend(["-stream_loop", "-1", "-t", str(scene_duration), "-i", bgm_file])
        bgm_index = input_index
        input_index += 1
        
        if duck_bgm or (narration_path and narration_placement == "over"):
            # Narrator-first: BGM is heavily ducked (0.2 volume) for atmospheric effect
            # BGM creates mood, narration tells the story
            duck_amount = 0.2  # Fixed 0.2 volume for narrator-first approach
            filter_parts.append(
                f"[{bgm_index}:a]volume={duck_amount},afade=t=in:d=0.5,afade=t=out:st={scene_duration-0.5}:d=0.5[bgm_ducked]"
            )
            audio_inputs.append("bgm_ducked")
        else:
            # No narration (rare case) - use normal BGM volume
            filter_parts.append(
                f"[{bgm_index}:a]volume=0.3,afade=t=in:d=0.5,afade=t=out:st={scene_duration-0.5}:d=0.5[bgm_vol]"
            )
            audio_inputs.append("bgm_vol")
    
    # Add Ambience (looped to scene duration)
    elif ambience_file and os.path.exists(ambience_file):
        inputs.extend(["-stream_loop", "-1", "-t", str(scene_duration), "-i", ambience_file])
        amb_index = input_index
        input_index += 1
        filter_parts.append(
            f"[{amb_index}:a]volume=0.2,afade=t=in:d=0.5,afade=t=out:st={scene_duration-0.5}:d=0.5[amb_vol]"
        )
        audio_inputs.append("amb_vol")
    
    # Add Impact SFX (at specific timestamp)
    if sfx_file and os.path.exists(sfx_file) and sfx_timestamp is not None:
        inputs.extend(["-itsoffset", str(sfx_timestamp), "-i", sfx_file])
        sfx_index = input_index
        input_index += 1
        filter_parts.append(f"[{sfx_index}:a]volume=0.8[sfx_vol]")
        audio_inputs.append("sfx_vol")
    
    # Add Intro Stinger (at start)
    elif intro_stinger and os.path.exists(intro_stinger):
        inputs.extend(["-i", intro_stinger])
        stinger_index = input_index
        input_index += 1
        filter_parts.append(f"[{stinger_index}:a]volume=0.6[stinger_vol]")
        audio_inputs.append("stinger_vol")
    
    # Add Outro Stinger (at end with offset)
    elif outro_stinger and os.path.exists(outro_stinger):
        # Get stinger duration to calculate offset
        stinger_dur_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            outro_stinger
        ]
        stinger_dur_result = subprocess.run(stinger_dur_cmd, capture_output=True, text=True)
        stinger_duration = float(stinger_dur_result.stdout.strip())
        stinger_offset = max(0, scene_duration - stinger_duration)
        
        inputs.extend(["-itsoffset", str(stinger_offset), "-i", outro_stinger])
        stinger_index = input_index
        input_index += 1
        filter_parts.append(f"[{stinger_index}:a]volume=0.6[stinger_vol]")
        audio_inputs.append("stinger_vol")
    
    # ═══════════════════════════════════════════════════════════
    # CHARACTER AUDIO (ATTACK + PERSONALITY)
    # ═══════════════════════════════════════════════════════════
    
    # Add Attack Audio (at specific timestamp, -4dB, never ducked)
    if attack_audio and os.path.exists(attack_audio) and attack_timestamp is not None:
        inputs.extend(["-itsoffset", str(attack_timestamp), "-i", attack_audio])
        attack_index = input_index
        input_index += 1
        filter_parts.append(f"[{attack_index}:a]volume=-4dB[attack_vol]")
        audio_inputs.append("attack_vol")
        print(f"🎯 Adding attack audio @ {attack_timestamp}s (-4dB)")
    
    # Add Personality Cue (at specific timestamp, -8dB)
    if personality_audio and os.path.exists(personality_audio) and personality_timestamp is not None:
        inputs.extend(["-itsoffset", str(personality_timestamp), "-i", personality_audio])
        personality_index = input_index
        input_index += 1
        filter_parts.append(f"[{personality_index}:a]volume=-8dB[personality_vol]")
        audio_inputs.append("personality_vol")
        print(f"🎭 Adding personality cue @ {personality_timestamp}s (-8dB)")
    
    # Final mix (max 4 audio layers: dialogue + attack/SFX + BGM + personality)
    if len(audio_inputs) > 1:
        mix_inputs = "".join(f"[{inp}]" for inp in audio_inputs)
        filter_parts.append(
            f"{mix_inputs}amix=inputs={len(audio_inputs)}:duration=longest:dropout_transition=0,volume=1.0[final_audio]"
        )
        audio_map = "[final_audio]"
    else:
        audio_map = audio_inputs[0] if audio_inputs else f"{dialogue_index}:a"
    
    # Combine filters
    filter_complex = ";".join(filter_parts) if filter_parts else None
    
    # Build final command
    cmd = ["ffmpeg", "-y"] + inputs
    
    if filter_complex:
        cmd.extend(["-filter_complex", filter_complex])
    
    cmd.extend([
        "-map", "0:v",  # Video from first input
        "-map", audio_map,  # Mixed audio
        "-c:v", "copy",  # Copy video codec
        "-c:a", "aac",  # Encode audio to AAC
        "-b:a", "192k",  # Audio bitrate
        output_path
    ])
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print(f"✅ Audio mixed: {output_path}")
    
    return output_path


def finalize_video(raw_video: str, output_filename: str) -> str:
    """
    Final processing and move to output directory.
    """
    final_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Simple copy if no further processing needed
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_video,
        "-c", "copy",
        final_path
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print(f"🎉 Final video: {final_path}")
    
    return final_path
