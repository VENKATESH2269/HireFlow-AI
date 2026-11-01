from datetime import datetime
from app.models import ApplicationEvent

ALLOWED_TRANSITIONS = {
    "APPLIED": {"SCREENING", "WITHDRAWN", "REJECTED"},
    "SCREENING": {"INTERVIEW", "WITHDRAWN", "REJECTED"},
    "INTERVIEW": {"OFFER", "WITHDRAWN", "REJECTED"},
    "OFFER": {"HIRED", "REJECTED", "WITHDRAWN"},
    "HIRED": set(), "REJECTED": set(), "WITHDRAWN": set(),
}


def transition_application(db, application, new_stage, actor="system", note=None):
    allowed = ALLOWED_TRANSITIONS.get(application.stage, set())
    if new_stage not in allowed:
        raise ValueError(f"Invalid transition: {application.stage} -> {new_stage}")
    old_stage = application.stage
    application.stage = new_stage
    db.add(ApplicationEvent(
        application_id=application.id,
        from_stage=old_stage,
        to_stage=new_stage,
        event_type="STAGE_TRANSITION",
        event_at=datetime(2026, 10, 30),
        actor=actor,
        note=note,
    ))
    return application
