# Audio Generation Setup Guide

## 🎵 Fully Automated Audio Generation

This system generates **BGM, SFX, ambience, and stingers** using AI models with **zero manual curation**.

---

## 📦 Installation

### Step 1: Install Audio Dependencies

```bash
pip install -r requirements_audio.txt
```

This installs:
- **MusicGen** (BGM + Stingers)
- **AudioLDM 2** (SFX + Ambience)
- **librosa** (Auto-curation)
- **pyloudnorm** (Loudness normalization)

### Step 2: Generate Audio Library (One-Time)

```bash
python scripts/generate_audio_assets.py
```

**What it does:**
- Generates 4 BGM loops (calm, tense, heroic, sad)
- Generates 4 SFX (punch, slash, explosion, hit)
- Generates 4 ambience tracks (wind, sea, crowd, room)
- Generates 2 stingers (intro, outro)

**Time:** 10-20 minutes on GPU (one-time only)

**Output:**
```
assets/
├── bgm/
│   ├── calm_loop.wav
│   ├── tense_loop.wav
│   ├── heroic_loop.wav
│   └── sad_loop.wav
├── sfx/
│   ├── punch.wav
│   ├── slash.wav
│   ├── explosion.wav
│   └── hit.wav
├── ambience/
│   ├── wind.wav
│   ├── sea.wav
│   ├── crowd.wav
│   └── room.wav
└── stingers/
    ├── intro.wav
    └── outro.wav
```

---

## 🤖 How Auto-Curation Works

### For BGM:
1. **Generate 5 variations** of each mood
2. **Auto-score each variation** using audio analysis:
   - Energy (RMS)
   - Tempo (BPM)
   - Brightness (Spectral Centroid)
   - Dynamic Range
   - Harmonic Content
3. **Pick highest-scoring variation**
4. **Auto-normalize to -14 LUFS** (YouTube-safe)
5. **Save to library**

**NO HUMAN INPUT REQUIRED**

### For SFX/Ambience:
1. **Generate using AudioLDM 2**
2. **Auto-normalize loudness**
3. **Save to library**

---

## 🔄 Manual Override (Optional)

If you want to replace any auto-generated file:

```bash
# Delete auto-generated file
rm assets/bgm/heroic_loop.wav

# Add your own file
cp my_better_heroic.wav assets/bgm/heroic_loop.wav

# Bot will use your version instead
```

**The generator skips files that already exist.**

---

## ⚡ Performance

**GPU Requirements:**
- MusicGen: ~4GB VRAM (small model)
- AudioLDM 2: ~6GB VRAM

**Generation Time (GPU):**
- BGM (30s): ~10-20 seconds per variation
- SFX (1s): ~2-5 seconds
- Ambience (30s): ~10-15 seconds

**CPU Mode:**
- Slower but works (5-10x slower)

---

## 🎬 Usage in Pipeline

Once generated, the pipeline automatically uses these assets:

```python
# Gemini says: "bgm": "heroic"
# Pipeline loads: assets/bgm/heroic_loop.wav
# (instant, no generation)
```

**Zero runtime overhead after initial generation.**

---

## 🆓 Alternative: Free Asset Libraries

If AI generation is too slow/resource-intensive, you can manually download:

- **Freesound.org** - Royalty-free SFX/ambience
- **Incompetech** - Royalty-free BGM
- **Zapsplat** - Free SFX library

Just place files in the correct folders with the correct names.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements_audio.txt

# 2. Generate audio library (one-time, 10-20 min)
python scripts/generate_audio_assets.py

# 3. Run your pipeline (uses generated assets)
python entrypoints/main.py --input manga.jpg
```

**That's it!** Fully automated, professional quality.
