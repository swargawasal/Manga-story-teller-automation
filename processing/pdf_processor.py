# processing/pdf_processor.py - Lean PDF to Image Conversion (PyMuPDF)
import os
import fitz  # PyMuPDF
from config.config import TEMP_DIR
from typing import List

def process_pdf(pdf_path: str) -> List[str]:
    """
    Converts a PDF to a list of page images using PyMuPDF.
    Saved in TEMP_DIR.
    """
    print(f"📄 Processing PDF with PyMuPDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    page_paths = []
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better OCR
        p_path = os.path.join(TEMP_DIR, f"page_{i}.png")
        pix.save(p_path)
        page_paths.append(p_path)
        
    doc.close()
    return page_paths
