from sqlalchemy import func
from app.models import Application, Feedback, Interview, Offer


def calculate_metrics(db):
    total_apps = db.query(Application).count()
    avg_score = db.query(func.avg(Application.screening_score)).scalar() or 0
    total_interviews = db.query(Interview).count()
    conflicts = db.query(Interview).filter(Interview.conflict_flag.is_(True)).count()
    total_feedback = db.query(Feedback).count()
    total_offers = db.query(Offer).count()
    accepted = db.query(Offer).filter(Offer.status == "ACCEPTED").count()
    return {
        "total_applications": total_apps,
        "average_screening_score": round(float(avg_score), 2),
        "total_interviews": total_interviews,
        "interview_conflict_rate_pct": round(conflicts / total_interviews * 100, 2) if total_interviews else 0,
        "feedback_records": total_feedback,
        "total_offers": total_offers,
        "accepted_offers": accepted,
        "offer_acceptance_rate_pct": round(accepted / total_offers * 100, 2) if total_offers else 0,
    }
