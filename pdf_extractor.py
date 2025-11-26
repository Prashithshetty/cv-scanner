"""
PDF Text Extractor - Comprehensive Script
Supports multiple extraction methods
"""

import os
import sys

def check_and_install_libraries():
    """Check and install required libraries"""
    libraries = {
        'PyPDF2': 'pypdf2',
        'pdfplumber': 'pdfplumber',
    }
    
    missing_libs = []
    
    for lib_name, pip_name in libraries.items():
        try:
            __import__(lib_name.lower())
        except ImportError:
            missing_libs.append(pip_name)
    
    if missing_libs:
        print("Missing libraries detected. Install them using:")
        print(f"pip install {' '.join(missing_libs)}")
        return False
    return True

class PDFTextExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.text = ""
        
    def extract_with_pypdf2(self):
        """Extract using PyPDF2"""
        try:
            import PyPDF2
            
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                text = ""
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page.extract_text()
                
                self.text = text
                return True
                
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            return False
    
    def extract_with_pdfplumber(self):
        """Extract using pdfplumber"""
        try:
            import pdfplumber
            
            text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text += f"\n--- Page {i + 1} ---\n"
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
            
            self.text = text
            return True
            
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            return False
    
    def extract(self, method='auto'):
        """
        Extract text using specified method
        
        Args:
            method: 'pypdf2', 'pdfplumber', or 'auto'
        """
        if not os.path.exists(self.pdf_path):
            print(f"Error: File not found: {self.pdf_path}")
            return False
        
        if method == 'auto' or method == 'pdfplumber':
            if self.extract_with_pdfplumber():
                print("✓ Extracted with pdfplumber")
                return True
        
        if method == 'auto' or method == 'pypdf2':
            if self.extract_with_pypdf2():
                print("✓ Extracted with PyPDF2")
                return True
        
        return False
    
    def save_to_file(self, output_path=None):
        """Save extracted text to file"""
        if not self.text:
            print("No text to save!")
            return
        
        if not output_path:
            output_path = self.pdf_path.replace('.pdf', '_extracted.txt')
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.text)
            print(f"✓ Text saved to: {output_path}")
        except Exception as e:
            print(f"Error saving file: {e}")
    
    def get_text(self):
        """Return extracted text"""
        return self.text

def main():
    print("PDF Text Extractor")
    print("=" * 50)
    
    # Check libraries
    if not check_and_install_libraries():
        return
    
    # Get PDF path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("Enter PDF file path: ").strip()
    
    # Create extractor
    extractor = PDFTextExtractor(pdf_path)
    
    # Extract text
    print("\nExtracting text...")
    if extractor.extract():
        # Get extracted text
        text = extractor.get_text()
        
        # Display preview
        print("\n--- Preview (first 500 characters) ---")
        print(text[:500] + "..." if len(text) > 500 else text)
        
        # Save option
        print("\n" + "-" * 50)
        save = input("Save full text to file? (y/n): ")
        if save.lower() == 'y':
            extractor.save_to_file()
    else:
        print("Failed to extract text from PDF")

if __name__ == "__main__":
    main()