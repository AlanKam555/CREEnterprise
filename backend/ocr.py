"""
CRE Enterprise Suite - OCR Module
Document scanning and text extraction
"""
import io
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

# OCR and Image Processing
try:
    from PIL import Image
    import pytesseract
    HAS_PIL = True
    HAS_OCR = True
except ImportError:
    HAS_PIL = False
    HAS_OCR = False

# PDF to Image
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMG = True
except ImportError:
    HAS_PDF2IMG = False

# PDF Text Extraction
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# Web scraping for screenshots
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_WEB = True
except ImportSoup:
    HAS_WEB = False


class OCRProcessor:
    """OCR processor for extracting text from images and documents"""
    
    @staticmethod
    def extract_text_from_image(image_data: bytes) -> Dict[str, Any]:
        """Extract text from image bytes"""
        if not HAS_OCR or not HAS_PIL:
            return {
                "status": "error",
                "error": "OCR not available. Install: pip install pytesseract pillow",
                "text": "",
                "data": {}
            }
        
        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image)
            
            # Parse structured data
            data = OCRProcessor._parse_rent_roll_text(text)
            
            return {
                "status": "success",
                "text": text,
                "data": data,
                "confidence": "medium"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "text": "",
                "data": {}
            }
    
    @staticmethod
    def extract_text_from_pdf(pdf_data: bytes) -> Dict[str, Any]:
        """Extract text from PDF bytes"""
        if not HAS_PDF:
            return {
                "status": "error",
                "error": "PDF extraction not available. Install: pip install PyPDF2",
                "text": "",
                "data": {}
            }
        
        try:
            buffer = io.BytesIO(pdf_data)
            reader = PyPDF2.PdfReader(buffer)
            
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            
            # Parse structured data
            data = OCRProcessor._parse_rent_roll_text(full_text)
            
            return {
                "status": "success",
                "text": full_text,
                "data": data,
                "pages": len(reader.pages)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "text": "",
                "data": {}
            }
    
    @staticmethod
    def _parse_rent_roll_text(text: str) -> Dict[str, Any]:
        """Parse rent roll data from extracted text"""
        entries = []
        
        # Common patterns for unit numbers
        unit_pattern = r'(?:Unit|unit|#|No\.?)\s*([A-Z0-9\-]+)'
        
        # Common patterns for tenant names
        tenant_patterns = [
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)+)',  # "John Smith"
            r'([A-Z][a-z]+(?:\'s)?)',  # "John's"
        ]
        
        # Common patterns for rent amounts
        rent_pattern = r'\$?([\d,]+(?:\.\d{2})?)\s*(?:per|/)?\s*(?:month|mo)?'
        
        # Common patterns for dates
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        
        # Extract lines that look like rent roll entries
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a rent roll entry
            has_rent = bool(re.search(rent_pattern, line, re.IGNORECASE))
            has_unit = bool(re.search(unit_pattern, line))
            
            if has_rent and has_unit:
                # Extract unit number
                unit_match = re.search(unit_pattern, line)
                unit = unit_match.group(1) if unit_match else ""
                
                # Extract rent amount
                rent_match = re.search(rent_pattern, line, re.IGNORECASE)
                rent_str = rent_match.group(1).replace(',', '') if rent_match else '0'
                rent = float(rent_str) if rent_str else 0
                
                # Extract dates
                dates = re.findall(date_pattern, line)
                
                entry = {
                    'unit_number': unit,
                    'monthly_rent': rent,
                    'lease_start': dates[0] if len(dates) > 0 else '',
                    'lease_end': dates[1] if len(dates) > 1 else '',
                    'status': 'occupied' if rent > 0 else 'vacant'
                }
                entries.append(entry)
        
        # Calculate summary
        total_units = len(entries)
        occupied = len([e for e in entries if e['status'] == 'occupied'])
        total_rent = sum(e['monthly_rent'] for e in entries)
        
        return {
            'entries': entries,
            'total_units': total_units,
            'occupied_units': occupied,
            'total_monthly_rent': total_rent,
            'occupancy_rate': round((occupied / total_units * 100) if total_units > 0 else 0, 2)
        }
    
    @staticmethod
    def extract_property_data(text: str) -> Dict[str, Any]:
        """Extract property information from text"""
        data = {}
        
        # Address patterns
        address_patterns = [
            r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl)[,\s]+[A-Za-z\s]+[,\s]+[A-Z]{2}\s+\d{5})',
            r'(\d+\s+[A-Za-z\s]+\d+[,\s]+[A-Za-z\s]+[,\s]+[A-Z]{2}\s+\d{5})',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['address'] = match.group(1)
                break
        
        # Price patterns
        price_patterns = [
            r'\$\s*([\d,]+(?:\.\d{2})?)',
            r'Price:\s*\$?([\d,]+)',
            r'Purchase\s*Price:\s*\$?([\d,]+)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                data['purchase_price'] = float(price_str)
                break
        
        # Asset type patterns
        asset_types = ['multifamily', 'industrial', 'mixed-use', 'commercial', 'land']
        text_lower = text.lower()
        for asset_type in asset_types:
            if asset_type in text_lower:
                data['asset_type'] = asset_type
                break
        
        return data
    
    @staticmethod
    def scan_screenshot(url: str) -> Dict[str, Any]:
        """Capture and OCR a webpage screenshot"""
        if not HAS_WEB or not HAS_OCR:
            return {
                "status": "error",
                "error": "Web scraping not available. Install: pip install requests beautifulsoup4"
            }
        
        try:
            # Take screenshot (requires screenshot API)
            # For now, just extract text from page
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            
            # Parse data from text
            rent_roll_data = OCRProcessor._parse_rent_roll_text(text)
            property_data = OCRProcessor.extract_property_data(text)
            
            return {
                "status": "success",
                "url": url,
                "text": text[:5000],  # First 5000 chars
                "rent_roll": rent_roll_data,
                "property": property_data
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class DocumentScanner:
    """Scanner for various document types"""
    
    @staticmethod
    def scan_lease(lease_text: str) -> Dict[str, Any]:
        """Extract key information from a lease document"""
        data = {}
        
        # Tenant name
        tenant_patterns = [
            r'Tenant:\s*([A-Z][a-z]+ [A-Z][a-z]+)',
            r'Name:\s*([A-Z][a-z]+ [A-Z][a-z]+)',
        ]
        for pattern in tenant_patterns:
            match = re.search(pattern, lease_text)
            if match:
                data['tenant_name'] = match.group(1)
                break
        
        # Lease dates
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        dates = re.findall(date_pattern, lease_text)
        if len(dates) >= 2:
            data['lease_start'] = dates[0]
            data['lease_end'] = dates[1]
        
        # Rent amount
        rent_pattern = r'(?:Rent|Monthly):\s*\$?([\d,]+(?:\.\d{2})?)'
        match = re.search(rent_pattern, lease_text, re.IGNORECASE)
        if match:
            data['monthly_rent'] = float(match.group(1).replace(',', ''))
        
        # Unit number
        unit_pattern = r'(?:Unit|Apartment|Suite):\s*([A-Z0-9\-]+)'
        match = re.search(unit_pattern, lease_text, re.IGNORECASE)
        if match:
            data['unit_number'] = match.group(1)
        
        return data
    
    @staticmethod
    def scan_market_report(report_text: str) -> Dict[str, Any]:
        """Extract market data from a report"""
        data = {}
        
        # Cap rates
        cap_rate_pattern = r'Cap\s*Rate[s]?:\s*([\d\.]+)%?'
        match = re.search(cap_rate_pattern, report_text, re.IGNORECASE)
        if match:
            data['cap_rate'] = float(match.group(1))
        
        # NOI
        noi_pattern = r'NOI:\s*\$?([\d,]+)'
        match = re.search(noi_pattern, report_text, re.IGNORECASE)
        if match:
            data['noi'] = float(match.group(1).replace(',', ''))
        
        # Price per unit
        price_pattern = r'\$\s*([\d,]+)\s*(?:per|/)\s*unit'
        match = re.search(price_pattern, report_text, re.IGNORECASE)
        if match:
            data['price_per_unit'] = float(match.group(1).replace(',', ''))
        
        return data
