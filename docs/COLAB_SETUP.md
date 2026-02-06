# Colab Setup Guide

## 🚀 Quick Start (Colab)

### Option 1: Using Colab Notebook (Recommended)

1. **Upload to Google Drive:**
   ```
   Upload colab_setup.ipynb to your Google Drive
   ```

2. **Open in Colab:**
   ```
   Right-click → Open with → Google Colaboratory
   ```

3. **Enable GPU:**
   ```
   Runtime → Change runtime type → GPU (T4)
   ```

4. **Run all cells:**
   ```
   Runtime → Run all
   ```

**That's it!** Everything auto-installs and runs.

---

## 🛠️ Option 2: Manual Setup (Local/Server)

### Linux/Mac:
```bash
bash setup.sh
```

### Windows:
```powershell
# Install dependencies
pip install -r requirements.txt
pip install -r requirements_visual.txt
pip install -r requirements_audio.txt

# Generate audio library (once)
python scripts/generate_audio_assets.py

# Run pipeline
python entrypoints/main.py --input manga.jpg
```

---

## 📋 What Gets Installed

### Core Dependencies:
- Gemini API client
- FFmpeg
- OpenCV
- NumPy, Pillow

### Tier-1 Visual:
- Real-CUGAN (2× upscaling)
- RIFE (48 FPS interpolation)

### Offline Audio:
- MusicGen-medium (BGM)
- AudioLDM 2 (SFX)
- librosa (auto-curation)
- pyloudnorm (normalization)

---

## ⏱️ Time Estimates (T4 GPU)

| Task | Time |
|:-----|:-----|
| **Install dependencies** | ~3-5 min |
| **Generate audio library** | ~5 min (one-time) |
| **Process one scene** | ~8-12s |

---

## 🔧 Troubleshooting

### Out of Memory:
```python
# Reduce batch size in config
BATCH_SIZE=1
```

### Slow generation:
```bash
# Check GPU
nvidia-smi

# Verify T4 GPU is active
```

### Missing dependencies:
```bash
# Reinstall
pip install --upgrade -r requirements.txt
```

---

## 📊 Colab Limits

**Free Tier:**
- 12 hours max session
- T4 GPU (16GB VRAM)
- ~50GB disk

**Pro Tier:**
- 24 hours max session
- Better GPU allocation
- ~200GB disk

**Recommendation:** Free tier is sufficient for this pipeline.

---

## 🎯 Production Checklist

- [ ] Upload `colab_setup.ipynb` to Drive
- [ ] Enable T4 GPU in Colab
- [ ] Set Gemini API key
- [ ] Run audio generation (once)
- [ ] Upload manga panels
- [ ] Run pipeline
- [ ] Download videos

**Ready to ship!** 🚀
