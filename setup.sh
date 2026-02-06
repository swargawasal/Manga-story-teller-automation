#!/bin/bash
# Production Setup Script for YouTube Automation
# Installs all dependencies for Tier-1 visual + offline audio generation

set -e  # Exit on error

echo "======================================================================"
echo "🚀 YOUTUBE AUTOMATION - PRODUCTION SETUP"
echo "======================================================================"
echo ""
echo "This will install:"
echo "  - Core dependencies"
echo "  - Tier-1 visual enhancement (Real-CUGAN, RIFE)"
echo "  - Offline audio generation (MusicGen, AudioLDM 2)"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"
echo ""

# Install core dependencies
echo "======================================================================"
echo "📦 Installing core dependencies..."
echo "======================================================================"
pip install -r requirements.txt

# Install visual enhancement dependencies
echo ""
echo "======================================================================"
echo "🎨 Installing Tier-1 visual dependencies..."
echo "======================================================================"
pip install -r requirements_visual.txt

# Install audio generation dependencies (offline only)
echo ""
echo "======================================================================"
echo "🎵 Installing offline audio generation dependencies..."
echo "======================================================================"
pip install -r requirements_audio.txt

# Verify installations
echo ""
echo "======================================================================"
echo "✅ INSTALLATION COMPLETE"
echo "======================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1️⃣  Generate audio library (OFFLINE, run once):"
echo "    python scripts/generate_audio_assets.py"
echo ""
echo "2️⃣  Run main pipeline:"
echo "    python entrypoints/main.py --input manga.jpg"
echo ""
echo "3️⃣  Enable Tier-1 visuals (optional):"
echo "    cp .env.visual .env"
echo "    # Set TIER1_VISUALS_ENABLED=true"
echo ""
echo "======================================================================"
echo "🎬 Setup complete! Ready for production."
echo "======================================================================"
