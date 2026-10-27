"""
DeviationIQ — Unit Tests for Pydantic Schemas

Tests schema validation rules per 15_Test_Plan.md §2:
  - ExtractedField & DeviationExtraction validation
  - RiskAssessment validation with valid & invalid severities
  - ConfirmAssessmentRequest & SendMessageRequest validation
  - Enum value constraints
"""

import pytest
from pydantic import ValidationError

from app.schemas import (
    Confidence,
    ConfirmRequest,
    DeviationExtraction,
    ExtractedField,
    MessageRequest,
    RiskAssessment,
    Severity,
)


def test_extracted_field_defaults():
    field = ExtractedField()
    assert field.value is None
    assert field.confidence == Confidence.LOW
    assert field.source_snippet is None


def test_extracted_field_valid():
    field = ExtractedField(
        value="Hyderabad Plant B2",
        confidence=Confidence.HIGH,
        source_snippet="Site: Hyderabad Plant B2",
    )
    assert field.value == "Hyderabad Plant B2"
    assert field.confidence == Confidence.HIGH
    assert field.source_snippet == "Site: Hyderabad Plant B2"


def test_deviation_extraction_defaults():
    extraction = DeviationExtraction()
    assert extraction.site_plant.value is None
    assert extraction.batch_lot.value is None
    assert extraction.detailed_description.value is None


def test_deviation_extraction_full():
    data = {
        "site_plant": {"value": "Building B2", "confidence": "high", "source_snippet": "B2"},
        "batch_lot": {"value": "LOT-998", "confidence": "high"},
        "title": {"value": "Temp spike", "confidence": "medium"},
    }
    extraction = DeviationExtraction(**data)
    assert extraction.site_plant.value == "Building B2"
    assert extraction.batch_lot.value == "LOT-998"
    assert extraction.title.value == "Temp spike"
    # Unspecified fields default cleanly to empty ExtractedField
    assert extraction.date_of_occurrence.value is None


def test_risk_assessment_valid():
    assessment = RiskAssessment(
        suggested_severity=Severity.MAJOR,
        suggested_impact="Product batch on hold; QA review required",
        reasoning="Exceeded 72C temp limit for 25 minutes",
    )
    assert assessment.suggested_severity == Severity.MAJOR
    assert "hold" in assessment.suggested_impact


def test_risk_assessment_invalid_severity():
    with pytest.raises(ValidationError):
        RiskAssessment(
            suggested_severity="Catastrophic",  # Invalid enum value
            suggested_impact="Impact",
            reasoning="Reasoning",
        )


def test_confirm_assessment_request_valid():
    req = ConfirmRequest(
        suggested_severity=Severity.CRITICAL,
        suggested_impact="Batch discarded",
        reasoning="Confirmed by supervisor",
        reviewed_by="Rajan Mehta (QA Lead)",
    )
    assert req.suggested_severity == Severity.CRITICAL
    assert req.reviewed_by == "Rajan Mehta (QA Lead)"


def test_send_message_request_validation():
    req = MessageRequest(text="Change batch to ABC-456")
    assert req.text == "Change batch to ABC-456"
