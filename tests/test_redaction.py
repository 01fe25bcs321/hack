from backend.app.services.documents.manager import DocumentManager


def test_public_redaction_covers_common_identifiers():
    source = {
        "summary": "Contact alex@example.com or +919876543210.",
        "claims": [{"claim": "Employee ID: EMP-2044; ID 1234 5678 9012"}],
    }
    result, count = DocumentManager._redact_public(source)
    serialized = str(result)
    assert count == 4
    assert "alex@example.com" not in serialized
    assert "+919876543210" not in serialized
    assert "EMP-2044" not in serialized
    assert "1234 5678 9012" not in serialized
