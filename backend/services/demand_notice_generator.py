from jinja2 import Template
from datetime import datetime
from typing import List
from backend.models.demand_notice import DemandNoticeRequest

class DemandNoticeGenerator:
    def __init__(self):
        self.template = Template("""
{{ date }}

{{ respondent_name }}
{{ respondent_address }}

Re: DEMAND NOTICE - {{ issue_description | truncate(50) }}

Dear {{ respondent_name }},

I am writing to formally notify you of a consumer protection issue that requires immediate attention.

BACKGROUND:
{{ issue_description }}

LEGAL BASIS:
Based on applicable consumer protection laws and relevant case precedents:
{% for case in case_references %}
- {{ case }}
{% endfor %}

DEMAND:
{{ resolution_sought }}
{% if amount_claimed %}
Amount Claimed: {{ amount_claimed }}
{% endif %}

You have thirty (30) days from receipt of this notice to respond and resolve this matter. Failure to respond may result in further legal action.

Please contact me at {{ complainant_contact }} to discuss resolution.

Sincerely,

{{ complainant_name }}
{{ complainant_address }}
{{ complainant_contact }}

---
DISCLAIMER: This notice is based on AI-generated legal research and should be reviewed by a qualified attorney before use.
        """)
    
    def generate_notice(self, request: DemandNoticeRequest, case_references: List[str]) -> str:
        """Generate a formal demand notice"""
        return self.template.render(
            date=datetime.now().strftime("%B %d, %Y"),
            respondent_name=request.respondent_name,
            respondent_address=request.respondent_address,
            complainant_name=request.complainant_name,
            complainant_address=request.complainant_address,
            complainant_contact=request.complainant_contact,
            issue_description=request.issue_description,
            resolution_sought=request.resolution_sought,
            amount_claimed=request.amount_claimed,
            case_references=case_references
        )