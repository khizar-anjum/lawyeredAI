from jinja2 import Template
from datetime import datetime
from typing import List, Dict, Any
from backend.models.demand_notice import DemandNoticeRequest
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io

class DemandNoticeGenerator:
    def __init__(self):
        # NYC Consumer Dispute Template
        self.template = Template("""# Demand Letter — NYC Consumer Dispute
---
## Header
- **From:** {{ complainant_name }}, {{ complainant_address }}, {{ complainant_contact }}
- **To:** {{ respondent_name }}, {{ respondent_address }}
---
## 1) Facts (brief)
- On **{{ incident_date }}**, I purchased **{{ item_service }}** for **${{ amount_claimed or "Amount" }}** from **{{ respondent_name }}**.
- The product/service was **{{ issue_type }}**.
- I attempted to resolve this on **{{ resolution_attempts }}** via **{{ contact_method }}**.
---
## 2) Amount Demanded
- **${{ amount_claimed or "Amount" }}**, itemized if helpful (purchase price, tax, delivery, other reasonable costs).
---
## 3) Legal Basis (plain language)
- **{{ legal_basis }}** resulting in financial loss.
- *Note:* NYC Small Claims Court hears money claims up to **$10,000**.
---
## 4) Remedy & Deadline
- Please remit **${{ amount_claimed or "Amount" }}** within **10 days** of receiving this letter to avoid filing in NYC Small Claims Court.
---
## 5) Attachments
- Copies of **receipt/invoice**
- Copies of **correspondence**
- **Photos/screenshots**
---
## Signature
- **{{ complainant_name }}** — {{ current_date }}
---
### Legal References
This demand is made pursuant to NYC Consumer Protection Law and NY General Business Law.

**DISCLAIMER:** This notice is based on AI-generated legal research and should be reviewed by a qualified New York attorney before use.
        """)
    
    def generate_notice(self, request: DemandNoticeRequest, case_references: List[str] = None) -> str:
        """Generate the demand notice using NYC template"""
        
        # Parse issue description to extract key details
        issue_details = self._parse_issue_description(request.issue_description)
        
        return self.template.render(
            current_date=datetime.now().strftime("%B %d, %Y"),
            complainant_name=request.complainant_name,
            complainant_address=request.complainant_address,
            complainant_contact=request.complainant_contact,
            respondent_name=request.respondent_name,
            respondent_address=request.respondent_address,
            amount_claimed=request.amount_claimed,
            incident_date=issue_details.get('incident_date', 'Recent date'),
            item_service=issue_details.get('item_service', 'product/service'),
            issue_type=issue_details.get('issue_type', 'defective / not delivered / not as described'),
            resolution_attempts=issue_details.get('resolution_attempts', 'multiple occasions'),
            contact_method=issue_details.get('contact_method', 'email / phone / in-store'),
            legal_basis=issue_details.get('legal_basis', 'breach of contract / defective goods'),
            case_references=case_references or []
        )
    
    def _parse_issue_description(self, description: str) -> Dict[str, str]:
        """Parse the issue description to extract template variables"""
        # Simple keyword-based parsing - can be enhanced with NLP
        details = {}
        
        description_lower = description.lower()
        
        # Determine issue type
        if any(word in description_lower for word in ['defective', 'broken', 'damaged', 'faulty']):
            details['issue_type'] = 'defective'
        elif any(word in description_lower for word in ['not delivered', 'never received', 'missing']):
            details['issue_type'] = 'not delivered'
        elif any(word in description_lower for word in ['not as described', 'different', 'misleading']):
            details['issue_type'] = 'not as described'
        else:
            details['issue_type'] = 'defective / not delivered / not as described'
        
        # Determine legal basis
        if any(word in description_lower for word in ['warranty', 'guarantee']):
            details['legal_basis'] = 'breach of warranty'
        elif any(word in description_lower for word in ['contract', 'agreement']):
            details['legal_basis'] = 'breach of contract'
        else:
            details['legal_basis'] = 'breach of contract / defective goods'
        
        # Extract item/service (simple approach)
        if any(word in description_lower for word in ['phone', 'smartphone', 'mobile']):
            details['item_service'] = 'smartphone'
        elif any(word in description_lower for word in ['laptop', 'computer']):
            details['item_service'] = 'computer'
        elif any(word in description_lower for word in ['car', 'vehicle', 'auto']):
            details['item_service'] = 'vehicle'
        elif any(word in description_lower for word in ['service', 'repair']):
            details['item_service'] = 'service'
        else:
            details['item_service'] = 'product/service'
        
        return details
    
    def generate_pdf(self, content: str, filename: str) -> bytes:
        """Generate PDF from markdown-style content"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor='#2c3e50'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceBefore=3,
            spaceAfter=3,
            leading=12
        )
        
        # Parse content and create PDF elements
        story = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
            elif line.startswith('# '):
                # Main title
                title_text = line[2:].replace('—', '—')  # Em dash
                story.append(Paragraph(title_text, title_style))
            elif line.startswith('## '):
                # Section heading
                heading_text = line[3:]
                story.append(Paragraph(f"<b>{heading_text}</b>", heading_style))
            elif line.startswith('- **'):
                # Bold bullet point
                bullet_text = line[2:]  # Remove '- '
                story.append(Paragraph(f"• {bullet_text}", normal_style))
            elif line.startswith('- '):
                # Regular bullet point
                bullet_text = line[2:]
                story.append(Paragraph(f"• {bullet_text}", normal_style))
            elif line.startswith('---'):
                # Horizontal line
                story.append(Spacer(1, 12))
            else:
                # Regular paragraph
                if line:
                    story.append(Paragraph(line, normal_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()