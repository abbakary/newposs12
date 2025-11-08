"""
Invoice document processing utility for extracting data from PDF and image files.
Handles OCR using pytesseract and PDF processing using PyMuPDF.
"""

import os
import logging
from decimal import Decimal
from pathlib import Path
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class InvoiceDataExtractor:
    """Extract invoice data from PDF and image files using OCR."""

    # Patterns for matching common invoice fields
    KEYWORDS_CUSTOMER_NAME = [
        "customer name", "customer:", "bill to", "sold to", "customer ref", "code no"
    ]
    KEYWORDS_CUSTOMER_ADDRESS = [
        "address", "location", "customer address", "bill to", "p.o.box", "dar", "dar-es-salaam"
    ]
    KEYWORDS_CUSTOMER_PHONE = [
        "tel", "phone", "telephone", "mobile", "contact"
    ]
    KEYWORDS_ITEMS = [
        "item", "description", "product", "service", "qty", "quantity"
    ]
    KEYWORDS_TOTALS = [
        "total", "subtotal", "gross", "net", "vat", "tax", "amount"
    ]
    KEYWORDS_REFERENCE = [
        "reference", "ref", "po", "order", "invoice no", "pi no", "pi-"
    ]

    def __init__(self, file_path=None, file_obj=None):
        """
        Initialize with either a file path or a file-like object.
        
        Args:
            file_path: Path to PDF or image file
            file_obj: File-like object (InMemoryUploadedFile from Django)
        """
        self.file_path = file_path
        self.file_obj = file_obj
        self.file_extension = None
        self._validate_file()

    def _validate_file(self):
        """Validate that file exists and is supported format.

        This method is defensive: it ensures uploaded file-like objects have
        a usable name and that the detected extension is supported. Raises
        a clear ValueError when input is invalid so callers can handle it.
        """
        if self.file_path:
            path = Path(self.file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {self.file_path}")
            self.file_extension = path.suffix.lower()
        elif self.file_obj:
            # Uploaded file objects from Django should have a .name attribute.
            name = getattr(self.file_obj, 'name', None)
            if not name:
                raise ValueError("Uploaded file is missing a name attribute")
            self.file_extension = Path(name).suffix.lower()
        else:
            raise ValueError("Either file_path or file_obj must be provided")

        supported = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']
        if self.file_extension not in supported:
            raise ValueError(f"Unsupported file format: {self.file_extension}")

    def extract_text(self) -> str:
        """Extract all text from the document using OCR."""
        try:
            if self.file_extension == '.pdf':
                return self._extract_text_from_pdf()
            else:
                return self._extract_text_from_image()
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""

    def _correct_image_orientation(self, img: Image.Image) -> Image.Image:
        """Try to detect orientation using tesseract OSD and rotate image to upright.

        If detection fails, return the original image.
        """
        try:
            osd = pytesseract.image_to_osd(img)
            import re
            m = re.search(r'Rotate:\s*([0-9]+)', osd)
            if not m:
                m = re.search(r'Orientation in degrees:\s*([0-9]+)', osd)
            if m:
                angle = int(m.group(1)) % 360
                if angle != 0:
                    # Rotate by negative angle to deskew to upright
                    return img.rotate(-angle, expand=True)
        except Exception:
            # If anything goes wrong, don't fail
            pass
        return img

    def _ocr_image_to_lines(self, img: Image.Image) -> str:
        """Perform layout-aware OCR using pytesseract.image_to_data to reconstruct
        horizontal lines from word bounding boxes. This avoids reading vertically
        arranged text when the OCR returns words out of horizontal order.
        """
        try:
            from pytesseract import Output
            data = pytesseract.image_to_data(img, lang='eng', output_type=Output.DICT, config='--psm 6')
            words = []
            n = len(data.get('text', []))
            for i in range(n):
                txt = (data['text'][i] or '').strip()
                if not txt:
                    continue
                left = int(data['left'][i] or 0)
                top = int(data['top'][i] or 0)
                words.append({'text': txt, 'left': left, 'top': top})

            if not words:
                return ''

            # Cluster words into rows by y coordinate (top) with tolerance
            rows = []  # list of (avg_top, [words])
            for w in words:
                placed = False
                for r in rows:
                    if abs(r[0] - w['top']) <= 12:
                        r[1].append(w)
                        # update avg top
                        r[0] = int(sum(x['top'] for x in r[1]) / len(r[1]))
                        placed = True
                        break
                if not placed:
                    rows.append([w['top'], [w]])

            # Sort rows by top, and words by left within each row
            rows.sort(key=lambda x: x[0])
            lines = []
            for r in rows:
                words_sorted = sorted(r[1], key=lambda x: x['left'])
                line = ' '.join(w['text'] for w in words_sorted)
                lines.append(line)

            return '\n'.join(lines)
        except Exception as e:
            logger.debug(f"Layout OCR failed, falling back to image_to_string: {e}")
            try:
                return pytesseract.image_to_string(img, lang='eng')
            except Exception:
                return ''

    def _extract_text_from_pdf(self) -> str:
        """Extract text from PDF using PyMuPDF.

        Strategy:
        - Try to extract text with PyMuPDF's get_text() (fast).
        - If extracted text looks empty or too short, rasterize each page and
          run OCR (pytesseract) on the rendered image. This handles scanned
          PDFs and rotated pages consistently. Uses layout-aware OCR to
          reconstruct horizontal lines.
        """
        try:
            if self.file_obj:
                try:
                    self.file_obj.seek(0)
                except Exception:
                    pass
                pdf_bytes = self.file_obj.read()
                if not pdf_bytes:
                    raise ValueError("Uploaded PDF file appears empty after reading")
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            else:
                doc = fitz.open(self.file_path)

            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                try:
                    text = page.get_text()
                except Exception:
                    text = ""

                # If extracted text is short, fallback to raster OCR for this page
                if not text or len(text.strip()) < 80:
                    try:
                        # Render page to an image at higher resolution
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        mode = "RGB" if pix.n < 4 else "RGBA"
                        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                        # Correct orientation via OSD
                        img = self._correct_image_orientation(img)
                        page_text = self._ocr_image_to_lines(img)
                    except Exception as e:
                        logger.debug(f"PDF page raster OCR failed: {e}")
                        page_text = text or ""
                else:
                    page_text = text

                full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"

            try:
                doc.close()
            except Exception:
                pass

            return full_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _extract_text_from_image(self) -> str:
        """Extract text from image using pytesseract.

        Read the uploaded file safely into a BytesIO to avoid issues with
        file-like wrappers that don't behave like regular file objects. Detect
        and fix orientation before OCR to avoid vertical/rotated text issues.
        """
        try:
            if self.file_obj:
                try:
                    self.file_obj.seek(0)
                except Exception:
                    pass
                raw = self.file_obj.read()
                if not raw:
                    raise ValueError("Uploaded image file appears empty after reading")
                img = Image.open(BytesIO(raw))
            else:
                img = Image.open(self.file_path)

            # Correct orientation using OSD if possible
            try:
                img = self._correct_image_orientation(img)
            except Exception:
                pass

            # Enhance image for better OCR
            img = img.convert('RGB')

            # Use pytesseract to extract text
            text = pytesseract.image_to_string(img, lang='eng')
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def extract_invoice_data(self) -> dict:
        """
        Extract structured invoice data from the document.
        
        Returns:
            dict with keys: customer_name, customer_phone, customer_address,
                           reference, items, subtotal, tax_amount, total_amount
        """
        text = self.extract_text()
        if not text:
            return {}

        # Clean and normalize text
        text_lower = text.lower()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        extracted_data = {
            'customer_name': self._extract_customer_name(text_lower, lines),
            'customer_phone': self._extract_customer_phone(text_lower, lines),
            'customer_address': self._extract_customer_address(text_lower, lines),
            'reference': self._extract_reference(text_lower, lines),
            'items': self._extract_items(text, lines),
            'subtotal': self._extract_amount(text_lower, 'subtotal|net value|net'),
            'tax_amount': self._extract_amount(text_lower, 'vat|tax|sales tax'),
            'total_amount': self._extract_amount(text_lower, r'(total|gross value)\s*:', strict=True),
        }

        return {k: v for k, v in extracted_data.items() if v is not None}

    def _extract_customer_name(self, text_lower: str, lines: list) -> str:
        """Extract customer name from text."""
        for keyword in self.KEYWORDS_CUSTOMER_NAME:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Find the line containing this keyword
                for i, line in enumerate(lines):
                    if keyword in line.lower():
                        # Try next line or extract from current line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and len(next_line) > 3:
                                return next_line
                        # Also check if the name is after the colon
                        if ':' in line:
                            name = line.split(':', 1)[1].strip()
                            if name and len(name) > 3:
                                return name

        # Fallback: look for capitalized names in first 10 lines
        for line in lines[:10]:
            words = line.split()
            if len(words) >= 2 and all(w[0].isupper() for w in words if len(w) > 1):
                return line
        
        return None

    def _extract_customer_phone(self, text_lower: str, lines: list) -> str:
        """Extract customer phone number from text."""
        import re

        for keyword in self.KEYWORDS_CUSTOMER_PHONE:
            for line in lines:
                if keyword in line.lower():
                    # Extract phone number pattern
                    phone_pattern = r'(\+?\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})'
                    match = re.search(phone_pattern, line)
                    if match:
                        return match.group(1).strip()

        return None

    def _extract_customer_address(self, text_lower: str, lines: list) -> str:
        """Extract customer address from text."""
        for keyword in self.KEYWORDS_CUSTOMER_ADDRESS:
            for i, line in enumerate(lines):
                if keyword in line.lower():
                    # Collect next 2-3 lines as address
                    address_lines = []
                    for j in range(i + 1, min(i + 4, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not any(kw in next_line.lower() for kw in ['tel', 'phone', 'email']):
                            address_lines.append(next_line)
                    if address_lines:
                        return ' '.join(address_lines)

        return None

    def _extract_reference(self, text_lower: str, lines: list) -> str:
        """Extract reference/PO number from text."""
        import re

        for keyword in self.KEYWORDS_REFERENCE:
            for line in lines:
                if keyword in line.lower():
                    # Extract reference number/code after colon or keyword
                    if ':' in line:
                        ref = line.split(':', 1)[1].strip()
                        if ref and len(ref) < 50:
                            return ref
                    # Extract alphanumeric code after keyword
                    pattern = f"{keyword}[:\\s]+([A-Z0-9-]+)"
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        return match.group(1)

        return None

    def _extract_items(self, text: str, lines: list) -> list:
        """Extract line items from invoice using flexible heuristics.

        The original strict regex often misses items in various formats. This
        implementation looks for amounts in each line and treats the last
        numeric amount as the line total, the preceding numeric as unit price or qty
        depending on context. It is intentionally permissive and returns an
        empty list when no items are confidently found.
        """
        import re

        items = []

        # Helper to find all amounts in a line (handles commas)
        amount_re = re.compile(r'(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{1,2})?')

        for line in lines:
            # Skip lines that are clearly header/meta
            low = line.lower()
            if any(kw in low for kw in ['customer', 'date', 'invoice', 'total', 'vat', 'subtotal', 'tel', 'fax', 'address']):
                continue

            # Find amounts
            amounts = amount_re.findall(line)
            if not amounts:
                continue

            # Choose last amount as total
            total_str = amounts[-1]
            total = self._parse_amount(total_str) or None

            qty = None
            unit_price = None

            if len(amounts) >= 2:
                # If there are at least two numbers, try to assign them
                # Heuristic: if the second last is small integer -> qty
                second_last = amounts[-2]
                try:
                    if '.' not in second_last and int(second_last) <= 1000:
                        qty = int(second_last)
                    else:
                        unit_price = self._parse_amount(second_last)
                except Exception:
                    unit_price = self._parse_amount(second_last)

            # Determine description by removing numbers and punctuation at end
            # Trim trailing amounts/columns
            desc = re.sub(r'\b' + re.escape(amounts[-1]) + r'\b\s*$', '', line).strip()
            # remove any leading item codes like '1.' or '01'
            desc = re.sub(r'^\d+\.?\s*', '', desc).strip()

            if not desc or len(desc) < 3:
                # fallback to whole line if description seems too short
                desc = line.strip()

            item = {
                'description': desc[:255],
                'quantity': qty or 1,
                'unit': 'NOS',
                'unit_price': unit_price or (total if qty == 1 else None),
                'total': total
            }

            items.append(item)

        # Do not return None; return empty list when nothing found
        return items

    def _extract_amount(self, text_lower: str, keyword_pattern: str, strict=False) -> Decimal:
        """
        Extract currency amount from text.
        
        Args:
            text_lower: Lowercase text to search in
            keyword_pattern: Regex pattern for the keyword
            strict: If True, only match if keyword appears right before amount
        """
        import re

        # Pattern for amounts: handles 100,000.00 or 100000.00 format
        amount_pattern = r'(\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{1,2})?'
        
        # Look for keyword followed by amount
        combined_pattern = f"{keyword_pattern}[:\\s]+{amount_pattern}"
        match = re.search(combined_pattern, text_lower)
        
        if match:
            amount_str = match.group(1) if ',' not in match.group(1) else match.group(1)
            try:
                # Remove commas and convert to Decimal
                amount_clean = amount_str.replace(',', '')
                return Decimal(amount_clean)
            except:
                pass

        return None

    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount string to Decimal."""
        try:
            clean = amount_str.replace(',', '').strip()
            return Decimal(clean) if clean else None
        except:
            return None


def process_uploaded_invoice_file(uploaded_file) -> dict:
    """
    Process an uploaded invoice file and extract data.

    Args:
        uploaded_file: Django InMemoryUploadedFile or TemporaryUploadedFile

    Returns:
        dict with extracted invoice data
    """
    if not uploaded_file:
        return {
            'success': False,
            'error': 'No uploaded file provided',
            'data': {}
        }

    try:
        # Defensive: ensure uploaded_file has a name attribute for extension detection
        if not getattr(uploaded_file, 'name', None):
            return {'success': False, 'error': 'Uploaded file missing name', 'data': {}}

        extractor = InvoiceDataExtractor(file_obj=uploaded_file)
        data = extractor.extract_invoice_data() or {}

        return {
            'success': True,
            'data': data
        }
    except Exception as e:
        logger.error(f"Error processing invoice file: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'data': {}
        }
