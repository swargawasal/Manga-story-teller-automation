# scene_grouper.py - Deterministic Panel Grouping
import cv2
import numpy as np
from typing import List, Dict

class SceneGrouper:
    def __init__(self):
        pass

    def group_panels(self, panel_paths: List[str]) -> List[List[str]]:
        """
        Groups panels into scenes using deterministic signal heuristics.
        Signals: Visual similarity, Dialogue continuity (simple here), Geometry.
        """
        if not panel_paths:
            return []

        scenes = [[panel_paths[0]]]
        
        for i in range(1, len(panel_paths)):
            prev_path = panel_paths[i-1]
            curr_path = panel_paths[i]
            
            # Simple visual similarity check: Color Histogram
            if self._is_visually_similar(prev_path, curr_path):
                scenes[-1].append(curr_path)
            else:
                scenes.append([curr_path])
                
        # Limit scene size to avoid overly long clips (deterministic cap)
        final_scenes = []
        for scene in scenes:
            while len(scene) > 4:
                final_scenes.append(scene[:4])
                scene = scene[4:]
            if scene:
                final_scenes.append(scene)
                
        return final_scenes

    def _is_visually_similar(self, path1: str, path2: str) -> bool:
        """Determines if two images are visually similar using histograms."""
        img1 = cv2.imread(path1)
        img2 = cv2.imread(path2)
        
        if img1 is None or img2 is None:
            return False
            
        hist1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        cv2.normalize(hist1, hist1)
        cv2.normalize(hist2, hist2)
        
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return similarity > 0.7  # Deterministic threshold
