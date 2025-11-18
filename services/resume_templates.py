from dataclasses import dataclass
from typing import List


@dataclass
class ResumeTemplate:
    """Simple description of a resume formatting template.

    This is intentionally lightweight for the MVP and can be
    extended later with richer layout/section rules.
    """

    id: str
    name: str
    description: str


def get_available_templates() -> List[ResumeTemplate]:
    """Return the small set of templates exposed in the MVP.

    These are used by the standalone Resume Formatter page and
    exposed via the /api/v1/resume-formatter/templates endpoint.
    """

    return [
        ResumeTemplate(
            id="ezest_client_docx",
            name="eZest Client CV (DOCX)",
            description=(
                "Client-ready eZest CV format with structured profile summary, "
                "tools & technologies, detailed work experience, other projects, "
                "education, and certifications. Output as DOCX (PDF planned)."
            ),
        ),
        ResumeTemplate(
            id="client_default",
            name="Client Default Resume",
            description=(
                "Clean, concise resume format suitable for most client "
                "submissions. Focuses on summary, experience, and key skills."
            ),
        ),
        ResumeTemplate(
            id="ats_friendly",
            name="ATS-Friendly Resume",
            description=(
                "Simplified layout aimed at Applicant Tracking Systems. "
                "Avoids complex columns/graphics and emphasizes keywords."
            ),
        ),
        ResumeTemplate(
            id="vendor_submission",
            name="Vendor Submission Resume",
            description=(
                "Format tailored for vendor or partner submissions, with "
                "clear project and client-history emphasis."
            ),
        ),
    ]
