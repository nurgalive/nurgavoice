#!/usr/bin/env python3
"""
Test script to verify Russian/Cyrillic text rendering in PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os

def setup_unicode_fonts():
    """Setup Unicode fonts for PDF generation"""
    try:
        # Try to register DejaVu Sans font which supports Cyrillic
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Arial Unicode MS.ttf',  # macOS
            'C:/Windows/Fonts/arial.ttf',  # Windows
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Unicode', font_path))
                print(f"Registered font: {font_path}")
                return True
                
        print("Warning: No Unicode font found, using built-in fonts. Cyrillic characters may not display correctly.")
        return False
        
    except Exception as e:
        print(f"Warning: Could not register Unicode font: {e}")
        return False

def create_unicode_styles():
    """Create paragraph styles with Unicode font support"""
    styles = getSampleStyleSheet()
    
    # Check if Unicode font is available
    font_available = False
    try:
        from reportlab.pdfbase.pdfmetrics import getFont
        getFont('Unicode')
        font_available = True
    except Exception:
        pass
    
    if font_available:
        # Create custom styles with Unicode font
        title_style = ParagraphStyle(
            'UnicodeTitle',
            parent=styles['Title'],
            fontName='Unicode',
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'UnicodeHeading1',
            parent=styles['Heading1'],
            fontName='Unicode',
            fontSize=14,
            spaceAfter=6,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'UnicodeNormal',
            parent=styles['Normal'],
            fontName='Unicode',
            fontSize=10,
            spaceAfter=6
        )
        
        return {
            'Title': title_style,
            'Heading1': heading_style,
            'Normal': normal_style
        }
    else:
        # Use default styles
        return {
            'Title': styles['Title'],
            'Heading1': styles['Heading1'],
            'Normal': styles['Normal']
        }

def test_russian_pdf():
    """Test Russian text in PDF"""
    
    # Setup fonts
    font_setup = setup_unicode_fonts()
    print(f"Font setup successful: {font_setup}")
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Get Unicode-compatible styles
    custom_styles = create_unicode_styles()
    
    # Test Russian text
    russian_text = """
    Привет мир. Сегодня хорошая погода, солнце светит ярко.
    Это тестовый текст для проверки поддержки кириллицы в PDF.
    Русские буквы должны отображаться правильно: абвгдеёжзийклмнопрстуфхцчшщъыьэюя.
    АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ.
    """
    
    # Title
    story.append(Paragraph("Test Russian Text / Тест русского текста", custom_styles['Title']))
    story.append(Spacer(1, 12))
    
    # Heading
    story.append(Paragraph("Русский текст / Russian Text", custom_styles['Heading1']))
    
    # Content - escape HTML characters
    escaped_text = russian_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    story.append(Paragraph(escaped_text, custom_styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Save to file
    with open('test_russian.pdf', 'wb') as f:
        f.write(buffer.getvalue())
    
    print("PDF generated successfully: test_russian.pdf")
    print(f"File size: {len(buffer.getvalue())} bytes")

if __name__ == "__main__":
    test_russian_pdf()
