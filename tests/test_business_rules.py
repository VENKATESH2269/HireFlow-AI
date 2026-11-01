from types import SimpleNamespace
from app.services.offer_management import validate_offer_salary
from app.services.workflow import ALLOWED_TRANSITIONS


def test_offer_salary_inside_band():
    req = SimpleNamespace(min_salary=500000, max_salary=1000000)
    assert validate_offer_salary(req, 750000)[0] is True


def test_offer_salary_outside_band():
    req = SimpleNamespace(min_salary=500000, max_salary=1000000)
    valid, reason = validate_offer_salary(req, 1100000)
    assert valid is False
    assert "outside approved band" in reason


def test_lifecycle_rejects_skipping_from_applied_to_hired():
    assert "HIRED" not in ALLOWED_TRANSITIONS["APPLIED"]


def test_lifecycle_allows_screening_to_interview():
    assert "INTERVIEW" in ALLOWED_TRANSITIONS["SCREENING"]
