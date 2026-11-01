# Schema and lifecycle notes

The authoritative executable schema is `app/models.py`. SQLAlchemy declares a
primary key for every table and foreign keys for every relationship. SQLite
enforces uniqueness constraints on candidate email, department name/cost center,
and the candidate-skill and requisition-skill bridge pairs.

Application stage history is stored in `application_events`; stage changes should
be appended as events, not treated as the only record of prior state.
The state-transition policy is in `app/services/workflow.py`.

Screening uses only job-related attributes: required skill coverage and years of
experience. No demographic attributes or proxies are generated or used.
