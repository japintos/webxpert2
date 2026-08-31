from app.services.ai.lead_detector import LeadDetector


def test_general_question_score():
    score, _ = LeadDetector().detect("Hola, ¿qué hacen?")
    assert score == 20


def test_specific_question_score():
    score, interest = LeadDetector().detect("Necesito un sistema para stock")
    assert score >= 50
    assert interest


def test_quote_request_score():
    score, _ = LeadDetector().detect("Necesito que me coticen una tienda online")
    assert score >= 80


def test_hire_score():
    score, _ = LeadDetector().detect("Quiero contratar")
    assert score >= 90
