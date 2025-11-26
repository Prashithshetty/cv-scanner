"""
PDF Text Extractor - Streamlined for CV Scanner
Simple and efficient PDF text extraction
"""

import os
from pathlib import Path
from typing import Optional


class PDFTextExtractor:
    """Lightweight PDF text extractor with fallback support"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF extractor
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.text = ""
    
    def extract(self) -> bool:
        """
        Extract text from PDF using best available method
        
        Returns:
            True if extraction succeeded, False otherwise
        """
        if not self.pdf_path.exists():
            return False
        
        # Try pdfplumber first (better accuracy for CVs)
        if self._extract_with_pdfplumber():
            return True
        
        # Fallback to PyPDF2
        if self._extract_with_pypdf2():
            return True
        
        return False
    
    def _extract_with_pdfplumber(self) -> bool:
        """Extract using pdfplumber (preferred method)"""
        try:
            import pdfplumber
            
            text_parts = []
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            self.text = "\n".join(text_parts)
            return bool(self.text.strip())
            
        except Exception:
            return False
    
    def _extract_with_pypdf2(self) -> bool:
        """Extract using PyPDF2 (fallback method)"""
        try:
            import PyPDF2
            
            text_parts = []
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            self.text = "\n".join(text_parts)
            return bool(self.text.strip())
            
        except Exception:
            return False
    
    def get_text(self) -> str:
        """
        Get extracted text
        
        Returns:
            Extracted text content
        """
        return self.text


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Quick helper function to extract text from PDF
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text or None if extraction failed
    """
    extractor = PDFTextExtractor(pdf_path)
    if extractor.extract():
        return extractor.get_text()
    return None


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    extractor = PDFTextExtractor(pdf_path)
    
    print(f"Extracting text from: {pdf_path}")
    
    if extractor.extract():
        text = extractor.get_text()
        print(f"\n✓ Successfully extracted {len(text)} characters")
        print(f"\nPreview (first 500 chars):\n{'-'*50}")
        print(text[:500])
        print(f"{'-'*50}")
    else:
        print("\n✗ Failed to extract text from PDF")
        sys.exit(1)