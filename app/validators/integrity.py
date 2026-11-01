from sqlalchemy import func
from app.models import (
    Application, Candidate, Department, Feedback, Interview, JobRequisition,
    Offer, ResumeArtifact
)


def run_integrity_checks(db):
    checks = {}
    checks["duplicate_candidate_ids"] = db.query(Candidate.id).group_by(
        Candidate.id).having(func.count(Candidate.id) > 1).count()
    checks["duplicate_application_ids"] = db.query(Application.id).group_by(
        Application.id).having(func.count(Application.id) > 1).count()
    checks["applications_missing_candidate"] = sum(
        1 for a in db.query(Application).all() if a.candidate is None
    )
    checks["applications_missing_requisition"] = sum(
        1 for a in db.query(Application).all() if a.requisition is None
    )
    checks["interviews_with_invalid_dates"] = db.query(Interview).filter(
        Interview.scheduled_end <= Interview.scheduled_start).count()
    checks["feedback_score_out_of_range"] = db.query(Feedback).filter(
        (Feedback.technical_score < 0) | (Feedback.technical_score > 5) |
        (Feedback.communication_score < 0) | (Feedback.communication_score > 5) |
        (Feedback.problem_solving_score < 0) | (Feedback.problem_solving_score > 5)
    ).count()
    checks["offers_outside_salary_band"] = sum(
        1 for offer in db.query(Offer).all()
        if offer.salary < offer.application.requisition.min_salary
        or offer.salary > offer.application.requisition.max_salary
    )
    checks["roles_closed_with_active_applications"] = sum(
        1 for req in db.query(JobRequisition).filter(
            JobRequisition.status == "CLOSED").all()
        if any(a.status == "ACTIVE" for a in req.applications)
    )
    checks["resume_artifacts"] = db.query(ResumeArtifact).count()
    checks["departments"] = db.query(Department).count()
    return checks
