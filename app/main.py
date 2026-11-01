from app.validators.anomalies import detect_anomalies
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import Base, engine, get_db
from app.models import (
    Department, JobRequisition, Candidate, Application, Interview,
    Offer, ApplicationEvent
)
from app.analytics.metrics import calculate_metrics
from app.validators.integrity import run_integrity_checks
from app.services.scheduling import has_interviewer_conflict
from app.services.offer_management import validate_offer_salary

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HireFlow AI",
    description="Recruitment Workflow and Intelligence Platform",
    version="1.0.0",
)


@app.get("/")
def home():
    return {"project": "HireFlow AI", "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/summary")
def summary(db: Session = Depends(get_db)):
    return {
        "departments": db.query(Department).count(),
        "requisitions": db.query(JobRequisition).count(),
        "candidates": db.query(Candidate).count(),
        "applications": db.query(Application).count(),
        "interviews": db.query(Interview).count(),
        "offers": db.query(Offer).count(),
    }


@app.get("/requisitions")
def list_requisitions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(JobRequisition).offset(skip).limit(min(limit, 200)).all()
    return [{
        "id": r.id, "title": r.title, "department": r.department.name,
        "status": r.status, "salary_band": [r.min_salary, r.max_salary]
    } for r in rows]


@app.get("/applications")
def list_applications(stage: str | None = None, skip: int = 0, limit: int = 50,
                      db: Session = Depends(get_db)):
    query = db.query(Application)
    if stage:
        query = query.filter(Application.stage == stage.upper())
    return [{
        "id": a.id, "candidate_id": a.candidate_id,
        "requisition_id": a.requisition_id, "stage": a.stage,
        "status": a.status, "screening_score": a.screening_score
    } for a in query.offset(skip).limit(min(limit, 200)).all()]


@app.get("/applications/{application_id}/history")
def application_history(application_id: str, db: Session = Depends(get_db)):
    app_record = db.get(Application, application_id)
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
    events = db.query(ApplicationEvent).filter(
        ApplicationEvent.application_id == application_id
    ).order_by(ApplicationEvent.id).all()
    return [{
        "from_stage": e.from_stage, "to_stage": e.to_stage,
        "event_type": e.event_type, "event_at": e.event_at,
        "actor": e.actor, "note": e.note
    } for e in events]


@app.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    return calculate_metrics(db)


@app.get("/validation")
def validation(db: Session = Depends(get_db)):
    return run_integrity_checks(db)


@app.get("/interviews/conflicts")
def interview_conflicts(db: Session = Depends(get_db)):
    rows = db.query(Interview).filter(Interview.conflict_flag.is_(True)).all()
    return [{
        "interview_id": i.id, "interviewer_id": i.interviewer_id,
        "application_id": i.application_id, "status": "CONFLICT"
    } for i in rows]


@app.get("/offers/outside-band")
def offers_outside_band(db: Session = Depends(get_db)):
    found = []
    for offer in db.query(Offer).all():
        valid, reason = validate_offer_salary(offer.application.requisition, offer.salary)
        if not valid:
            found.append({"offer_id": offer.id, "reason": reason})
    return found
@app.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    return detect_anomalies(db)
