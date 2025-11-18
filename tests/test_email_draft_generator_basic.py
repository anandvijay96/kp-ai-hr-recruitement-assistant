import json

from services.email_draft_generator import EmailDraftGenerator


class DummyUsage:
    total_token_count = 123


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.usage_metadata = DummyUsage()


class DummyModel:
    def __init__(self, text: str) -> None:
        self._text = text

    def generate_content(self, prompt: str, generation_config: dict) -> DummyResponse:  # type: ignore[name-defined]
        return DummyResponse(self._text)


class DummyTracker:
    def __init__(self) -> None:
        self.calls = []

    def can_make_request(self, provider: str):
        # Always allow requests in tests
        return True, None

    def track_request(
        self,
        provider: str,
        success: bool,
        tokens_used: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        self.calls.append(
            {
                "provider": provider,
                "success": success,
                "tokens_used": tokens_used or (input_tokens + output_tokens),
            }
        )


def _build_minimal_candidates() -> list[dict]:
    return [
        {
            "name": "Alice",
            "location": "Hyderabad",
            "skills": ["Python", "FastAPI"],
            "work_experience": [
                {"company": "Acme", "title": "Developer", "duration_months": 24},
            ],
            "professional_summary": "Backend engineer with API experience.",
        }
    ]


def test_build_prompt_respects_summary_style_flag():
    """_build_prompt should include different guidance for short vs detailed summaries."""

    gen = EmailDraftGenerator()
    candidates = _build_minimal_candidates()

    prompt_short = gen._build_prompt(  # type: ignore[protected-access]
        client_name="Client",
        requirement_title="Backend Developer",
        job_code="JD-1",
        job_description="Build APIs",
        candidates=candidates,
        force_table=False,
        allow_table_for_single=False,
        signature=None,
        tone="professional",
        rate_card=None,
        notice_period=None,
        location=None,
        detailed_summaries=False,
        prompt_hint=None,
    )

    prompt_detailed = gen._build_prompt(  # type: ignore[protected-access]
        client_name="Client",
        requirement_title="Backend Developer",
        job_code="JD-1",
        job_description="Build APIs",
        candidates=candidates,
        force_table=False,
        allow_table_for_single=False,
        signature=None,
        tone="professional",
        rate_card=None,
        notice_period=None,
        location=None,
        detailed_summaries=True,
        prompt_hint=None,
    )

    # Uses en-dash characters in text (2–3 and 4–6)
    assert "2–3 lines" in prompt_short
    assert "4–6 lines" in prompt_detailed


def test_generate_email_draft_appends_signature_once(monkeypatch):
    """Signature should be appended once to both text and HTML bodies."""

    # Patch the Redis usage tracker used inside the generator
    dummy_tracker = DummyTracker()
    monkeypatch.setattr(
        "services.email_draft_generator.get_redis_tracker",
        lambda: dummy_tracker,
    )

    # Prepare a generator with a dummy model that returns fixed JSON text
    gen = EmailDraftGenerator()

    base_body_text = "Hi Client,\n\nHere are a couple of profiles for your review."
    base_body_html = "<p>Hi Client,</p><p>Here are a couple of profiles for your review.</p>"

    response_payload = {
        "subject": "Profiles for Backend Developer",
        "body_text": base_body_text,
        "body_html": base_body_html,
        "candidates_table_html": None,
        "metadata": {},
    }

    gen.model = DummyModel(json.dumps(response_payload))

    signature = "Best regards,\nHR Team"

    draft = gen.generate_email_draft(
        client_name="Client",
        requirement_title="Backend Developer",
        job_code="JD-1",
        job_description="Backend developer role",
        candidates=_build_minimal_candidates(),
        force_table=False,
        allow_table_for_single=False,
        signature=signature,
        tone="professional",
    )

    body_text = draft["body_text"]
    body_html = draft["body_html"]

    # Signature text should be present exactly once in both representations
    assert signature in body_text
    assert body_text.count("Best regards") == 1

    assert "HR Team" in body_html
    assert body_html.lower().count("hr team") == 1

    # Tracker should have recorded a successful request
    assert any(call["success"] for call in dummy_tracker.calls)
