from app.models import Interview


def has_interviewer_conflict(db, interviewer_id, start, end, exclude_id=None):
    query = db.query(Interview).filter(
        Interview.interviewer_id == interviewer_id,
        Interview.status != "CANCELLED",
        Interview.scheduled_start < end,
        Interview.scheduled_end > start,
    )
    if exclude_id:
        query = query.filter(Interview.id != exclude_id)
    return query.first() is not None
