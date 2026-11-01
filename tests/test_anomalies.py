from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Department,
    JobRequisition,
    Candidate,
    Application,
    Interviewer,
    Interview,
    Offer
)
from app.validators.anomalies import detect_anomalies


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    session = TestingSession()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_detects_all_five_anomalies(db):

    now = datetime(2026, 11, 1, 10, 0)

    # Create department
    department = Department(
        id=1,
        name="Engineering",
        cost_center="ENG-001"
    )

    db.add(department)

    # Create closed requisition
    requisition = JobRequisition(
        id="REQ-TEST-001",
        department_id=1,
        title="Python Developer",
        location="Bengaluru",
        employment_type="FULL_TIME",
        status="CLOSED",
        min_salary=500000,
        max_salary=1000000,
        approved_by="HR Manager",
        approved_at=now,
        created_at=now
    )

    # Create candidate
    candidate = Candidate(
        id="CAND-TEST-001",
        full_name="Test Candidate",
        email="test@example.com",
        city="Bengaluru",
        years_experience=3,
        created_at=now
    )

    db.add_all([requisition, candidate])
    db.flush()

    # Create interviewer
    interviewer = Interviewer(
        id="IVR-TEST-001",
        full_name="Test Interviewer",
        department_id=1,
        active=True
    )

    db.add(interviewer)
    db.flush()

    # Create duplicate applications
    application1 = Application(
        id="APP-TEST-001",
        requisition_id=requisition.id,
        candidate_id=candidate.id,
        applied_at=now,
        stage="INTERVIEW",
        status="ACTIVE",
        screening_score=85,
        duplicate_flag=False
    )

    application2 = Application(
        id="APP-TEST-002",
        requisition_id=requisition.id,
        candidate_id=candidate.id,
        applied_at=now + timedelta(minutes=1),
        stage="APPLIED",
        status="ACTIVE",
        screening_score=80,
        duplicate_flag=True
    )

    db.add_all([application1, application2])
    db.flush()

    # Create overlapping interviews
    interview1 = Interview(
        id="INT-TEST-001",
        application_id=application1.id,
        interviewer_id=interviewer.id,
        round_number=1,
        scheduled_start=now + timedelta(hours=1),
        scheduled_end=now + timedelta(hours=2),
        status="SCHEDULED",
        conflict_flag=False
    )

    interview2 = Interview(
        id="INT-TEST-002",
        application_id=application1.id,
        interviewer_id=interviewer.id,
        round_number=2,
        scheduled_start=now + timedelta(hours=1, minutes=30),
        scheduled_end=now + timedelta(hours=2, minutes=30),
        status="SCHEDULED",
        conflict_flag=False
    )

    db.add_all([interview1, interview2])
    db.flush()

    # Create an offer outside the approved salary band
    offer = Offer(
        id="OFF-TEST-001",
        application_id=application1.id,
        salary=1500000,
        status="PENDING",
        approved_by="HR Manager",
        approved_at=now,
        issued_at=now
    )

    db.add(offer)
    db.commit()

    # Run anomaly detection
    results = detect_anomalies(db)

    detected_types = {
        result["issue_type"]
        for result in results
    }

    # Verify all five anomaly categories
    expected_types = {
        "DUPLICATE_APPLICATION",
        "INTERVIEWER_UNAVAILABLE",
        "MISSING_FEEDBACK_STAGE_ADVANCED",
        "OFFER_OUTSIDE_APPROVED_BAND",
        "CLOSED_ROLE_ACTIVE_APPLICATIONS"
    }

    assert expected_types.issubset(detected_types)


def test_no_anomalies_in_empty_database(db):

    results = detect_anomalies(db)

    assert results == []