# 🤖 Production Comic Bot - Colab Final Cell
# 1. Install System Dependencies
!apt-get install -y ffmpeg poppler-utils
!pip install easyocr edge-tts pdf2image google-generativeai opencv-python-headless torch torchvision torchaudio requests

# 2. Setup environment and imports
import sys
import os
import torch
import subprocess
from google.colab import userdata, files

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.getcwd())))

# Setup GEMINI key
os.environ["GEMINI_API_KEY"] = userdata.get('GEMINI_API_KEY')
os.environ["BOT_FPS"] = "24"

# Import from the new structure
from pipeline.main_pipeline import ComicAutomationPipeline

# 3. Final Verification
def verify_gpu():
    print("--- 🛠️ Colab T4 Verification ---")
    gpu_avail = torch.cuda.is_available()
    print(f"✅ GPU Available: {gpu_avail}")
    if gpu_avail:
        print(f"✅ Device: {torch.cuda.get_device_name(0)}")
    
    ffmpeg_ver = subprocess.check_output(["ffmpeg", "-version"]).decode().split('\n')[0]
    print(f"✅ FFmpeg: {ffmpeg_ver}")

verify_gpu()

# 4. Run Process
print("\n🚀 Ready for Demo. Please upload a Manga PDF, Image, or provide a URL.")
uploaded = files.upload()
if uploaded:
    input_file = list(uploaded.keys())[0]
    pipeline = ComicAutomationPipeline()
    output_video = pipeline.run_pipeline(input_file)
    files.download(output_video)
else:
    print("❌ No file uploaded.")
