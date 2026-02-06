# panel_detector.py - OpenCV-based Panel Extraction
import cv2
import numpy as np
import os
from typing import List, Tuple
from config.config import PANEL_CONFIDENCE_THRESHOLD, TEMP_DIR

class PanelDetector:
    def __init__(self):
        pass

    def detect_panels(self, image_path: str) -> List[Tuple[int, int, int, int]]:
        """
        Detect panels using contour detection.
        Returns list of (x, y, w, h) bounding boxes.
        """
        img = cv2.imread(image_path)
        if img is None:
            return []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Adaptive thresholding to handle various page backgrounds
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Morphological operations to join nearby lines and remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        page_area = img.shape[0] * img.shape[1]
        panels = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            panel_area = w * h
            confidence = panel_area / page_area

            # Only accept panels within a reasonable size range
            if 0.05 < confidence < 0.95:
                panels.append((x, y, w, h))

        # Fallback Logic
        if not panels:
            panels = self._apply_fallbacks(img)

        # Sort panels: Top-to-Bottom, then Left-to-Right
        # We use a y-threshold to group lines
        y_threshold = 50
        panels.sort(key=lambda b: (b[1] // y_threshold, b[0]))

        return panels

    def _apply_fallbacks(self, img) -> List[Tuple[int, int, int, int]]:
        """Applies fallback splits if no panels detected."""
        h, w = img.shape[:2]
        # Fallback 1: Wide spread -> vertical split
        if w > h * 1.5:
            return [(0, 0, w//2, h), (w//2, 0, w//2, h)]
        # Fallback 2: Tall page -> horizontal split
        if h > w * 1.5:
            return [(0, 0, w, h//2), (0, h//2, w, h//2)]
        # Fallback 3: Single panel
        return [(0, 0, w, h)]

    def extract_and_save_panels(self, image_path: str, output_prefix: str) -> List[str]:
        """Extracts panels and saves them as individual files."""
        img = cv2.imread(image_path)
        panels = self.detect_panels(image_path)
        paths = []

        for i, (x, y, w, h) in enumerate(panels):
            panel_img = img[y:y+h, x:x+w]
            path = os.path.join(TEMP_DIR, f"{output_prefix}_panel_{i}.png")
            cv2.imwrite(path, panel_img)
            paths.append(path)
            
        return paths
