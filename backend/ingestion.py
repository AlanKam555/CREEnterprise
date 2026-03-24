"""
CRE Enterprise Suite - Data Ingestion Engine
OCR, PDF Parsing, Excel Import, and Screenshot Processing
"""
import re
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import io

# ============ DATA CLASSES ============
@dataclass
class ExtractedField:
    value: Any
    confidence: float
    source: str
    raw_text: str

@dataclass
class IngestionResult:
    success: bool
    document_id: str
    document_type: str
    extracted_fields: Dict[str, ExtractedField]
    raw_text: str
    pages: int
    warnings: List[str]
    errors: List[str]

# ============ TEXT EXTRACTION ============
class TextExtractor:
    """Extract structured data from raw text using regex patterns."""
    
    PATTERNS = {
        # Currency amounts
        "purchase_price": [
            r"(?:purchase\s*price|purchase\s*price|acquisition\s*price|price|consideration)[:\s]*\\$([0-9,]+(?:\.\d{2})?)",
            r"\$\s*([0-9,]+(?:\.\d{2})?)\s*(?:million|m)?\s*(?:USD|\$)",
            r"([0-9,]+(?:\.\d{2})?)\s*(?:million|m)\s*(?:USD|\$)?",
        ],
        "monthly_rent": [
            r"(?:monthly\s*rent|rent\s*per\s*month|monthly\s*income|rent)[:\s]*\\$?([0-9,]+)",
            r"\\$([0-9,]+)\s*/\s*mo",
            r"\\$([0-9,]+)\s*(?:per\s*month|monthly)",
        ],
        "annual_rent": [
            r"(?:annual\s*rent|Gross\s*Potential\s*Rent|GPR|annual\s*income)[:\s]*\\$?([0-9,]+)",
        ],
        "noi": [
            r"(?:NOI|net\s*operating\s*income|NOI\s*\(pro\s*forma\))[:\s]*\\$?([0-9,]+(?:\.\d{2})?)",
            r"NOI[:\s]*([0-9,]+)",
        ],
        "cap_rate": [
            r"cap(?:itation)?\s*rate[:\s]*([0-9.]+)%",
            r"([0-9.]+)%\s*cap",
            r"cap\s*rate\s*of\s*([0-9.]+)",
        ],
        "vacancy_rate": [
            r"(?:vacancy|vacancy\s*rate|occupancy)[:\s]*([0-9.]+)%",
            r"([0-9.]+)%\s*(?:vacant|vacancy|occupancy)",
        ],
        "total_units": [
            r"(?:total\s*)?(?:unit|unit)s?[:\s]*(\d+)",
            r"(\d+)\s*(?:unit|units)",
        ],
        "sqft": [
            r"([0-9,]+)\s*(?:sq\.?\s*ft\.?|square\s*feet|sqft|SF)",
            r"(?:SF|sqft)[:\s]*([0-9,]+)",
        ],
        "address": [
            r"\d+\s+[\w\s]+(?:st|street|ave|avenue|blvd|boulevard|rd|road|dr|drive|lane|ln|court|ct)[\s,]+[\w\s]+(?:[\w\s]+,)?\s*[A-Z]{2}\s*\d{5}",
            r"\d+\s+[\w\s]+,\s*[\w\s]+,\s*[A-Z]{2}\s*\d{5}",
        ],
        "year_built": [
            r"(?:year\s*built|built\s*in|construction)[:\s]*(?:19|20)\d{2}",
            r"(?:19|20)\d{2}\s*(?:vintage|year)",
        ],
        "loan_amount": [
            r"(?:loan|debt|financing|mortgage)[:\s]*\\$?([0-9,]+(?:\.\d{2})?)",
            r"\\$([0-9,]+(?:\.\d{2})?)\s*(?:loan|mortgage|debt)",
        ],
        "interest_rate": [
            r"(?:interest\s*rate|rate)[:\s]*([0-9.]+)%",
            r"([0-9.]+)%\s*(?:interest|rate)",
        ],
        "lease_start": [
            r"(?:lease\s*start|commencement)[:\s]*(\d{1,2}[/-]\d{1,2}[/-](?:19|20)\d{2})",
        ],
        "lease_end": [
            r"(?:lease\s*end|expiration|expiry|termination)[:\s]*(\d{1,2}[/-]\d{1,2}[/-](?:19|20)\d{2})",
        ],
        "tenant_name": [
            r"(?:tenant|lessee|occupant)[:\s]*([A-Z][A-Za-z\s&]+?)(?:\s*(?:rent|suite|unit|lease)|$)",
        ],
        "unit_number": [
            r"(?:suite|unit|#)\s*([A-Z]?\d+[A-Z]?)|(?:unit|suite)\s*(\d+)",
        ],
        "email": [
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        ],
        "phone": [
            r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        ],
    }
    
    def extract(self, text: str) -> Dict[str, ExtractedField]:
        """Extract all known fields from text."""
        results = {}
        
        for field, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
                if matches:
                    raw = matches[0].group(0)
                    value = self._parse_value(matches[0].group(1) if len(matches[0].groups()) > 0 else raw, field)
                    if value is not None:
                        results[field] = ExtractedField(
                            value=value,
                            confidence=min(0.9, 0.6 + 0.1 * len(matches)),
                            source=f"regex:{pattern[:30]}",
                            raw_text=raw,
                        )
                        break
        
        return results
    
    def _parse_value(self, raw: str, field: str) -> Any:
        """Parse raw match string into appropriate Python type."""
        if not raw:
            return None
        
        # Remove common noise
        raw = raw.strip()
        
        if field in ["purchase_price", "monthly_rent", "annual_rent", "noi", "loan_amount"]:
            # Remove $ and commas, handle millions
            raw = raw.replace("$", "").replace(",", "").strip()
            if raw.lower().endswith(("million", "m")):
                return float(re.sub(r'[^\d.]', '', raw)) * 1_000_000
            try:
                return float(re.sub(r'[^\d.]', '', raw))
            except:
                return None
        
        elif field in ["cap_rate", "vacancy_rate", "interest_rate"]:
            try:
                return float(re.sub(r'[^\d.]', '', raw))
            except:
                return None
        
        elif field in ["total_units"]:
            try:
                return int(re.sub(r'[^\d]', '', raw))
            except:
                return None
        
        elif field in ["sqft"]:
            try:
                return int(re.sub(r'[^\d]', '', raw))
            except:
                return None
        
        elif field in ["year_built"]:
            match = re.search(r'(19|20)\d{2}', raw)
            return int(match.group()) if match else None
        
        return raw

# ============ RENT ROLL PARSER ============
class RentRollParser:
    """Parse rent roll tables from text."""
    
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """Extract rent roll entries from raw text."""
        entries = []
        
        # Try to find table-like structures
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Skip headers
            if any(h in line.lower() for h in ['tenant', 'unit', 'suite', 'rent', 'lease', '-----', '=====', 'header']):
                continue
            
            # Look for lines that could be rent roll entries
            entry = self._parse_line(line)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single rent roll line."""
        # Clean line
        line = re.sub(r'\s+', ' ', line).strip()
        if not line or len(line) < 10:
            return None
        
        parts = [p.strip() for p in re.split(r'[\t|]', line)]
        
        entry = {}
        
        # Try to extract unit number
        unit_match = re.search(r'(?:unit|suite|#)\s*([A-Z]?\d+[A-Z]?)', line, re.I)
        if unit_match:
            entry['unit_number'] = unit_match.group(1)
        
        # Try to extract monthly rent
        rent_match = re.search(r'\$?\s*([\d,]+(?:\.\d{2})?)\s*(?:/\s*mo|per\s*month|monthly|mont)', line, re.I)
        if rent_match:
            entry['monthly_rent'] = float(rent_match.group(1).replace(',', ''))
        
        # Try to extract tenant name (words before rent amount)
        tenant_match = re.search(r'^([A-Za-z][A-Za-z\s&\'.]+?)\s+(?:\$|\d)', line)
        if tenant_match and len(tenant_match.group(1)) > 2:
            entry['tenant_name'] = tenant_match.group(1).strip()
        
        # Try to extract lease dates
        lease_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-](?:19|20)\d{2})', line)
        if lease_match:
            entry['lease_end'] = lease_match.group(1)
        
        # Only return if we found meaningful data
        if len(entry) >= 2:
            entry['status'] = 'occupied' if entry.get('monthly_rent') else 'vacant'
            return entry
        
        return None
    
    def merge_with_property(self, entries: List[Dict], property_id: str) -> List[Dict]:
        """Prepare entries for database insertion."""
        return [
            {
                "id": str(uuid.uuid4())[:12],
                "property_id": property_id,
                "unit_number": e.get('unit_number', ''),
                "tenant_name": e.get('tenant_name', ''),
                "monthly_rent": e.get('monthly_rent', 0),
                "status": e.get('status', 'occupied'),
                "lease_end": e.get('lease_end', ''),
            }
            for e in entries
        ]

# ============ DOCUMENT INGESTOR ============
class DocumentIngestor:
    """Main ingestion pipeline."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent / "cre.db")
        self.text_extractor = TextExtractor()
        self.rent_roll_parser = RentRollParser()
    
    async def ingest_text(self, text: str, filename: str = "Manual Entry") -> IngestionResult:
        """Ingest raw text (from PDF, screenshot, or manual paste)."""
        doc_id = str(uuid.uuid4())[:12]
        warnings = []
        errors = []
        
        # Extract fields
        extracted = self.text_extractor.extract(text)
        
        # Try to parse rent roll table
        rent_entries = self.rent_roll_parser.parse(text)
        
        # Determine document type
        doc_type = self._classify_document(text, extracted)
        
        # Auto-populate suggestions
        suggestions = self._generate_suggestions(extracted, doc_type)
        
        # Store in DB
        self._store_document(doc_id, filename, text, extracted, doc_type, rent_entries)
        
        return IngestionResult(
            success=True,
            document_id=doc_id,
            document_type=doc_type,
            extracted_fields=extracted,
            raw_text=text[:500] + "..." if len(text) > 500 else text,
            pages=1,
            warnings=warnings,
            errors=errors,
        )
    
    def _classify_document(self, text: str, fields: Dict) -> str:
        """Classify the document type based on content."""
        text_lower = text.lower()
        
        # High-confidence indicators
        if any(k in text_lower for k in ['rent roll', 'tenant', 'lease', 'unit', 'suite']):
            if re.search(r'unit|suite|tenant|rent', text_lower):
                return 'rent_roll'
        
        if any(k in text_lower for k in ['purchase agreement', 'sale', 'closing', 'escrow']):
            return 'purchase_agreement'
        
        if any(k in text_lower for k in ['noi', 'net operating income', 'pro forma', 'cash flow']):
            return 'financial_statement'
        
        if any(k in text_lower for k in ['cap rate', 'valuation', 'irr', 'return']):
            return 'valuation_report'
        
        # Field-based classification
        if 'purchase_price' in fields and 'noi' in fields:
            return 'property_summary'
        
        if 'monthly_rent' in fields and 'tenant_name' in fields:
            return 'lease_agreement'
        
        if 'cap_rate' in fields and 'total_units' in fields:
            return 'property_summary'
        
        return 'unknown'
    
    def _generate_suggestions(self, fields: Dict, doc_type: str) -> Dict[str, Any]:
        """Generate auto-fill suggestions for forms."""
        suggestions = {}
        
        if doc_type in ['rent_roll', 'lease_agreement']:
            suggestions['property'] = {
                'monthly_rent': fields.get('monthly_rent'),
                'estimated_annual_rent': fields.get('annual_rent'),
            }
        
        if doc_type == 'property_summary':
            suggestions['property'] = {
                'purchase_price': fields.get('purchase_price'),
                'noi': fields.get('noi'),
                'cap_rate': fields.get('cap_rate'),
                'units': fields.get('total_units'),
                'sqft': fields.get('sqft'),
            }
        
        return suggestions
    
    def _store_document(self, doc_id: str, filename: str, text: str, 
                        fields: Dict, doc_type: str, rent_entries: List):
        """Store ingested document in database."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Create documents table if needed
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT,
                doc_type TEXT,
                raw_text TEXT,
                extracted JSON,
                rent_entries JSON,
                source TEXT,
                created_at TEXT
            )
        """)
        
        conn.execute("""
            INSERT INTO documents (id, filename, doc_type, raw_text, extracted, rent_entries, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            filename,
            doc_type,
            text[:10000],  # Limit text size
            json.dumps({k: asdict(v) for k, v in fields.items()}),
            json.dumps(rent_entries),
            'manual_ingestion',
            datetime.utcnow().isoformat(),
        ))
        
        conn.commit()
        conn.close()
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a stored document."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        doc = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        conn.close()
        
        if doc:
            d = dict(doc)
            if d.get('extracted'):
                d['extracted'] = json.loads(d['extracted'])
            if d.get('rent_entries'):
                d['rent_entries'] = json.loads(d['rent_entries'])
            return d
        return None
    
    def list_documents(self, doc_type: str = None, limit: int = 50) -> List[Dict]:
        """List all ingested documents."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT id, filename, doc_type, source, created_at FROM documents"
        params = []
        if doc_type:
            query += " WHERE doc_type=?"
            params.append(doc_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        docs = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(d) for d in docs]


# ============ PDF PROCESSOR (No external deps beyond stdlib) ============
class PDFProcessor:
    """Process PDFs using pdf-parse (already in requirements)."""
    
    def __init__(self):
        self.ingestor = DocumentIngestor()
    
    async def process_pdf(self, file_path: str, filename: str = None) -> IngestionResult:
        """Process a PDF file and extract structured data."""
        try:
            import pdf_parse
            
            with open(file_path, 'rb') as f:
                data = pdf_parse(f)
            
            # Combine all pages
            full_text = data.get('text', '')
            
            # Ingest through the main pipeline
            result = await self.ingestor.ingest_text(full_text, filename or file_path)
            result.pages = data.get('numpages', 1)
            
            return result
            
        except Exception as e:
            return IngestionResult(
                success=False,
                document_id="",
                document_type="error",
                extracted_fields={},
                raw_text="",
                pages=0,
                warnings=[],
                errors=[str(e)],
            )
