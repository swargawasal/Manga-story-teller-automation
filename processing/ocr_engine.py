# ocr_engine.py - EasyOCR implementation optimized for GPU
import easyocr
import torch
import cv2
from typing import List, Dict
from config.config import OCR_LANGUAGES, USE_GPU

class OCREngine:
    def __init__(self):
        # Initialize EasyOCR reader
        # gpu=True will use T4 GPU if available
        self.reader = easyocr.Reader(OCR_LANGUAGES, gpu=USE_GPU)
        print(f"🤖 OCR Engine Initialized (GPU: {USE_GPU and torch.cuda.is_available()})")

    def perform_ocr(self, image_path: str) -> List[Dict]:
        """
        Performs OCR on the given image.
        Returns list of results: {'text': str, 'box': list, 'confidence': float}
        """
        results = self.reader.readtext(image_path)
        extracted = []
        for (bbox, text, prob) in results:
            extracted.append({
                'text': text,
                'box': [int(x) for point in bbox for x in point], # Flatten box
                'confidence': float(prob)
            })
        return extracted

    def get_full_text(self, image_path: str) -> str:
        """Returns all text found in the image as a single string."""
        results = self.perform_ocr(image_path)
        return " ".join([res['text'] for res in results])
