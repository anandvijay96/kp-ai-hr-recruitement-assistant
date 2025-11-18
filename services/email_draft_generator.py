"""Email draft generation using Google Gemini

This service takes client/vendor context, job description, and candidate profiles
and generates a ready-to-use email draft (subject, body, optional HTML table)
for HR to send to clients.

It reuses the existing Redis-based LLM usage tracker and Gemini setup
used elsewhere in the project.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from core.config import settings
from services.llm_usage_tracker_redis import get_redis_tracker

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:  # pragma: no cover - dependency may be optional in some envs
    GEMINI_AVAILABLE = False
    logger.warning("Google Gemini not available. Install: pip install google-generativeai")


class EmailDraftGenerator:
    """Generate client-ready email drafts using an LLM (Gemini)."""

    def __init__(self, provider: str = "gemini", api_key: Optional[str] = None) -> None:
        self.provider = provider.lower()
        self.api_key = api_key or getattr(settings, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY")
        self.model = None

        if self.provider == "gemini" and GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
            logger.info("✅ EmailDraftGenerator initialized with Gemini 2.5 Flash-Lite")
        else:
            if not GEMINI_AVAILABLE:
                logger.warning("Gemini provider not available for EmailDraftGenerator")
            elif not self.api_key:
                logger.warning("Gemini API key not configured for EmailDraftGenerator")

    def _build_prompt(
        self,
        *,
        client_name: str,
        requirement_title: Optional[str],
        job_code: Optional[str],
        job_description: str,
        candidates: List[Dict[str, Any]],
        force_table: bool,
        allow_table_for_single: bool,
        signature: Optional[str],
        tone: str,
        rate_card: Optional[str] = None,
        notice_period: Optional[str] = None,
        location: Optional[str] = None,
        detailed_summaries: bool = False,
        prompt_hint: Optional[str] = None,
    ) -> str:
        """Build the prompt for the LLM.

        "candidates" is a list of dicts with keys like:
        - id, name, email, location, professional_summary
        - skills: List[str]
        - work_experience: List[Dict[str, Any]] (subset fields only)
        """

        requirement_label = requirement_title or "the requirement"

        has_rate_card = bool(rate_card and rate_card.strip())
        has_notice_period = bool(notice_period and notice_period.strip())
        has_location = bool(location and location.strip())

        summary_style_note = (
            "Keep each candidate summary concise (around 2–3 lines) focusing on the strongest experience, tech stack, and current role."
            if not detailed_summaries
            else "Write more detailed candidate summaries (around 4–6 lines) including key projects, responsibilities, technologies, and notable achievements."
        )

        custom_instructions = (
            prompt_hint.strip()
            if prompt_hint and prompt_hint.strip()
            else "No extra custom instructions were provided."
        )

        # Serialize candidate info in a simple, deterministic way
        candidate_blocks: List[str] = []
        for idx, c in enumerate(candidates, start=1):
            skills = ", ".join(c.get("skills", [])[:10]) if c.get("skills") else ""
            exp_entries = c.get("work_experience") or []
            total_months = sum(int(e.get("duration_months") or 0) for e in exp_entries)
            total_years = round(total_months / 12, 1) if total_months > 0 else None
            exp_label = f"Approximately {total_years} years of experience" if total_years is not None else "Experience details available in profile"

            block_lines = [
                f"Candidate {idx}: {c.get('name') or 'Unknown'}",
                f"Location: {c.get('location') or 'Not specified'}",
                exp_label,
            ]

            if skills:
                block_lines.append(f"Key skills: {skills}")

            summary = c.get("professional_summary")
            if summary:
                block_lines.append(f"Professional summary: {summary}")

            block_lines.append("Work experience (high level):")
            for exp in exp_entries[:3]:
                company = exp.get("company") or "Company"
                title = exp.get("title") or "Role"
                duration = exp.get("duration_months")
                duration_label = f" (~{duration} months)" if duration else ""
                block_lines.append(f"- {title} at {company}{duration_label}")

            candidate_blocks.append("\n".join(block_lines))

        candidates_text = "\n\n".join(candidate_blocks)

        table_rule_multi = "ALWAYS include an HTML table for the candidates when there are 2 or more candidates."
        table_rule_single = (
            "For a single candidate, include the HTML table ONLY if `include_table_for_single` is true; "
            "otherwise do not include the table in the email body and return null for candidates_table_html."
        )
        base_columns = [
            "S.No",
            "Job Code",
            "Candidate Name",
            "Experience",
            "Skills",
        ]

        if has_rate_card:
            base_columns.append("Rate Card")
        if has_notice_period:
            base_columns.append("Notice Period")
        if has_location:
            base_columns.append("Location")

        table_columns_text = ", ".join(base_columns)

        if signature and signature.strip():
            signature_note = (
                "Do NOT include any explicit closing signature block (name, title, company). "
                "Finish with a polite closing sentence only; the HR signature text will be appended separately."
            )
        else:
            signature_note = (
                "You may end with a polite closing sentence (e.g., 'Looking forward to your feedback.') "
                "but DO NOT invent any person name or company signature."
            )

        if has_rate_card or has_notice_period or has_location:
            table_meta_lines = [
                "Optional common values for some table columns (apply the same value to each candidate row):",
            ]
            if has_rate_card:
                table_meta_lines.append(f"- Rate Card (same for all candidates): {rate_card.strip()}")
            if has_notice_period:
                table_meta_lines.append(f"- Notice Period (same for all candidates): {notice_period.strip()}")
            if has_location:
                table_meta_lines.append(f"- Location (same for all candidates): {location.strip()}")
            table_meta_block = "\n".join(table_meta_lines)
        else:
            table_meta_block = (
                "No fixed values were provided for Rate Card, Notice Period, or Location. "
                "You may leave those cells empty or use a simple placeholder like '--'."
            )

        prompt = f"""
You are an expert HR coordinator drafting client submission emails.

Write a clear, concise email to a client named "{client_name}" about candidate profiles for {requirement_label}.

Tone: {tone}

Job Code (if provided): {job_code or 'N/A'}

Job Description:
{job_description}

Candidate Profiles (raw data, summarise as needed):
{candidates_text}

Additional common field hints for the candidate table:
{table_meta_block}

IMPORTANT OUTPUT RULES:
1. You MUST return ONLY valid JSON (no markdown, no comments, no extra text).
2. JSON schema:
{{
  "subject": "Short, clear subject line mentioning role and number of profiles",
  "body_text": "Plain text version of the email body, using numbered list for candidates.",
  "body_html": "HTML email body with greeting, intro paragraph, numbered candidate summaries, and optional HTML table.",
  "candidates_table_html": "HTML <table> ONLY for the candidate table (no <html>, <body>, or other content) or null if not required.",
  "has_table": true or false,
  "metadata": {{
     "candidate_count": {len(candidates)},
     "force_table": {str(force_table).lower()},
     "allow_table_for_single": {str(allow_table_for_single).lower()}
  }}
}}

TABLE RULES:
- {table_rule_multi}
- {table_rule_single}
- The table columns should be: {table_columns_text}.
- The table should have simple, visible borders between cells so that it is easy to read in common email clients (you can use border="1" or inline CSS on the <table> and cells).
- For any column that is present but has missing data for some candidates, you may leave the cell as an empty string or a simple placeholder like "--".
- Do NOT duplicate the entire email inside candidates_table_html. It must contain ONLY the <table> element.
- If no optional inputs (Rate Card, Notice Period, Location) are provided, omit those columns entirely from the table.

EMAIL CONTENT RULES:
- Start with a short greeting (e.g., "Hi <Client Name>," and one-line greeting).
- Mention the role and that you are sharing profiles for their review.
- {summary_style_note}
- Use numbered formatting (1., 2., 3.) for candidate blurbs to match typical HR submission style.
- Be specific and professional but not overly verbose.
- Do NOT invent details not implied by the data; keep statements grounded.
- {signature_note}

Custom HR instructions (if any, follow them in addition to the rules above):
{custom_instructions}

Return ONLY the JSON object with the fields described above.
"""

        return prompt

    def generate_email_draft(
        self,
        *,
        client_name: str,
        requirement_title: Optional[str],
        job_code: Optional[str],
        job_description: str,
        candidates: List[Dict[str, Any]],
        force_table: bool,
        allow_table_for_single: bool,
        signature: Optional[str],
        tone: str,
        rate_card: Optional[str] = None,
        notice_period: Optional[str] = None,
        location: Optional[str] = None,
        detailed_summaries: bool = False,
        prompt_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate an email draft using Gemini.

        Returns a dict compatible with EmailDraftResponse.
        """

        if not self.model:
            raise RuntimeError("Email draft generator is not configured (Gemini model not available)")

        tracker = get_redis_tracker()
        can_proceed, warning = tracker.can_make_request("gemini")
        if not can_proceed:
            raise RuntimeError(warning or "Gemini quota exceeded")
        if warning:
            logger.warning(warning)

        prompt = self._build_prompt(
            client_name=client_name,
            requirement_title=requirement_title,
            job_code=job_code,
            job_description=job_description,
            candidates=candidates,
            force_table=force_table,
            allow_table_for_single=allow_table_for_single,
            signature=signature,
            tone=tone,
            rate_card=rate_card,
            notice_period=notice_period,
            location=location,
            detailed_summaries=detailed_summaries,
            prompt_hint=prompt_hint,
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.35,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                },
            )

            tokens_used = 0
            if hasattr(response, "usage_metadata") and getattr(response.usage_metadata, "total_token_count", None) is not None:
                tokens_used = int(response.usage_metadata.total_token_count)

            tracker.track_request("gemini", success=True, tokens_used=tokens_used)

            result_text = (response.text or "").strip()

            # Strip markdown code fences if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()

            data = json.loads(result_text)

            subject = data.get("subject") or "Profiles for your requirement"
            body_text = data.get("body_text") or ""
            body_html = data.get("body_html") or body_text
            candidates_table_html = data.get("candidates_table_html")
            has_table = bool(candidates_table_html)

            # Ensure the provided signature is present in both text and HTML bodies,
            # while avoiding obvious duplication when the model already added it.
            if signature and signature.strip():
                sig = signature.strip()

                # Use the first non-empty signature line for duplicate checks
                sig_lines = [l.strip() for l in sig.splitlines() if l.strip()]
                sig_first = sig_lines[0] if sig_lines else sig

                # Check the last part of the body for an existing signature line
                tail_window = 300
                body_tail_lower = body_text[-tail_window:].lower()

                if sig_first.lower() not in body_tail_lower:
                    if body_text.strip():
                        body_text = body_text.rstrip() + "\n\n" + sig
                    else:
                        body_text = sig

                sig_html = "<br>".join(sig.splitlines())
                body_html_tail_lower = body_html[-tail_window:].lower()
                if (
                    sig_first.lower() not in body_html_tail_lower
                    and sig_html.lower() not in body_html_tail_lower
                ):
                    if body_html.strip():
                        body_html = body_html.rstrip() + "<br><br>" + sig_html
                    else:
                        body_html = sig_html

            metadata = data.get("metadata") or {}
            metadata.setdefault("candidate_count", len(candidates))
            metadata.setdefault("provider", self.provider)
            metadata.setdefault("model", "gemini-2.5-flash-lite")

            return {
                "subject": subject,
                "body_text": body_text,
                "body_html": body_html,
                "candidates_table_html": candidates_table_html,
                "has_table": has_table,
                "metadata": metadata,
            }

        except json.JSONDecodeError as e:
            tracker.track_request("gemini", success=False)
            logger.error(f"Failed to parse email draft JSON: {e}")
            logger.error(f"Raw response: {result_text[:500]}")
            raise
        except Exception as e:  # pragma: no cover - defensive logging
            tracker.track_request("gemini", success=False)
            logger.error(f"Gemini email draft generation failed: {e}", exc_info=True)
            raise
