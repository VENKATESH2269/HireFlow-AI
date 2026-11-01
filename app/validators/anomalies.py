from collections import defaultdict

from app.models import (
    Application,
    Feedback,
    Interview,
    JobRequisition,
    Offer
)

from app.services.scheduling import has_interviewer_conflict
from app.services.offer_management import validate_offer_salary


def detect_anomalies(db):

    results = []

    # 1. Detect duplicate applications
    pairs = defaultdict(list)

    applications = db.query(Application).all()

    for app in applications:
        key = (app.requisition_id, app.candidate_id)
        pairs[key].append(app.id)

    for (req_id, candidate_id), ids in pairs.items():

        if len(ids) > 1:
            results.append({
                "issue_type": "DUPLICATE_APPLICATION",
                "record_id": ids[-1],
                "related_ids": ids,
                "details": (
                    f"Candidate {candidate_id} applied multiple times "
                    f"for {req_id}"
                )
            })

    # 2. Detect interviewer scheduling conflicts
    interviews = db.query(Interview).filter(
        Interview.status != "CANCELLED"
    ).all()

    for interview in interviews:

        conflict = has_interviewer_conflict(
            db,
            interview.interviewer_id,
            interview.scheduled_start,
            interview.scheduled_end,
            exclude_id=interview.id
        )

        if conflict:
            results.append({
                "issue_type": "INTERVIEWER_UNAVAILABLE",
                "record_id": interview.id,
                "related_ids": [interview.interviewer_id],
                "details": "Interviewer has overlapping interview bookings"
            })

    # 3. Detect missing feedback after interview progression
    applications = db.query(Application).filter(
        Application.stage.in_(["INTERVIEW", "OFFER", "HIRED"])
    ).all()

    for app in applications:

        for interview in app.interviews:

            feedback_count = db.query(Feedback).filter(
                Feedback.interview_id == interview.id
            ).count()

            if feedback_count == 0:
                results.append({
                    "issue_type": "MISSING_FEEDBACK_STAGE_ADVANCED",
                    "record_id": app.id,
                    "related_ids": [interview.id],
                    "details": (
                        "Application progressed without interview feedback"
                    )
                })

    # 4. Detect offers outside approved salary bands
    offers = db.query(Offer).all()

    for offer in offers:

        valid, reason = validate_offer_salary(
            offer.application.requisition,
            offer.salary
        )

        if not valid:
            results.append({
                "issue_type": "OFFER_OUTSIDE_APPROVED_BAND",
                "record_id": offer.id,
                "related_ids": [offer.application_id],
                "details": reason
            })

    # 5. Detect closed requisitions with active applications
    requisitions = db.query(JobRequisition).filter(
        JobRequisition.status == "CLOSED"
    ).all()

    for req in requisitions:

        active_applications = [
            app.id for app in req.applications
            if app.status == "ACTIVE"
        ]

        if active_applications:
            results.append({
                "issue_type": "CLOSED_ROLE_ACTIVE_APPLICATIONS",
                "record_id": req.id,
                "related_ids": active_applications,
                "details": (
                    "Closed requisition still has active applications"
                )
            })

    return results