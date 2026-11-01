# HireFlow AI — Data Dictionary

All IDs are immutable strings unless noted. Dates/times use ISO 8601 in exports.
Synthetic records only. Enum values are uppercase.

| Entity | Primary key | Fields and validation |
|---|---|---|
| Department | id (integer) | name required/unique; cost_center required/unique |
| JobRequisition | id (`REQ-2026-000001`) | department_id FK; title, location, employment_type required; status OPEN/CLOSED/CANCELLED; min_salary/max_salary positive and max >= min; approver and approval/creation timestamps required |
| Candidate | id (`CAND-000001`) | full_name/email/city required; email unique; years_experience >= 0 |
| Application | id (`APP-<req>-<candidate>`) | requisition_id and candidate_id FKs; applied_at required; stage/status enums; screening_score 0–100; duplicate_flag boolean |
| ResumeArtifact | id (`RES-CAND-000001`) | candidate_id unique FK; file_type PDF/DOCX; file_size_kb positive; source SYNTHETIC |
| Skill | id integer | name required/unique |
| CandidateSkill | id integer | candidate_id and skill_id FKs; unique pair; proficiency BEGINNER/INTERMEDIATE/ADVANCED; years_used >= 0 |
| RequisitionSkill | id integer | requisition_id and skill_id FKs; unique pair; importance > 0 |
| ScreeningRule | id integer | requisition_id FK; min_experience >= 0; minimum_score 0–100; skill_weight + experience_weight = 1; effective dates |
| Interview | id (`INT-2026-000001`) | application_id/interviewer_id FKs; round_number >= 1; end > start; status SCHEDULED/COMPLETED/CANCELLED; conflict_flag boolean |
| Interviewer | id (`IVR-0001`) | full_name and department_id FK required; active boolean |
| Feedback | id (`FB-<interview-id>-<interviewer-id>`) | interview_id/interviewer_id FKs; scores 1–5; recommendation STRONG_YES/YES/MAYBE/NO; comments and submitted_at required |
| Offer | id (`OFF-2026-000001`) | application_id FK; salary positive and within approved band for valid offers; status PENDING/ACCEPTED/REJECTED; approver and timestamps required |
| ApplicationEvent | id integer | application_id FK; from_stage nullable; to_stage, event_type, event_at, actor required; append-only history |

## Relationship cardinality
Department 1:N requisitions and interviewers. Requisition N:M Skill via RequisitionSkill.
Candidate N:M Skill via CandidateSkill. Requisition 1:N Applications and ScreeningRules.
Candidate 1:N Applications and 1:1 ResumeArtifact. Application 1:N Interviews,
Offers and ApplicationEvents. Interview 1:N Feedback. Interviewer 1:N Interviews
and Feedback. Feedback can be absent until submitted. Offer response_at is optional
while pending. ScreeningRule effective_to is optional for current rules.
