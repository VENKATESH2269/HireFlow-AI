"""Deterministic synthetic data generator for HireFlow AI.
Run: python scripts/generate_data.py --seed 20261022
     python scripts/generate_data.py --seed 20261022 --scale 0.1
"""
import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

import pandas as pd
from faker import Faker
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import Base, engine, SessionLocal
from app.models import (
    Department, JobRequisition, Candidate, Skill, RequisitionSkill,
    CandidateSkill, ResumeArtifact, ScreeningRule, Application, Interviewer,
    Interview, Feedback, Offer, ApplicationEvent
)
from app.services.screening import score_candidate

SEED = 20261022
SKILLS = [
    "Python", "SQL", "FastAPI", "Java", "JavaScript", "React", "Docker",
    "AWS", "Machine Learning", "Pandas", "Git", "Linux", "REST APIs",
    "Data Analysis", "Communication", "System Design"
]
DEPARTMENTS = ["Engineering", "Data", "Product", "Operations", "AI Research"]
TITLES = ["Python Backend Engineer", "AI Engineer", "Data Analyst",
          "Software Engineer", "ML Engineer", "Platform Engineer"]
CITIES = ["Bengaluru", "Hyderabad", "Pune", "Chennai", "Remote"]
STAGES = ["APPLIED", "SCREENING", "INTERVIEW", "REJECTED", "WITHDRAWN", "OFFER", "HIRED"]


def stable_id(prefix, number, width=6):
    return f"{prefix}{number:0{width}d}"


def dump_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    pd.DataFrame(rows).to_csv(path, index=False)


def export_table(session, model, filename):
    rows = []
    for obj in session.query(model).all():
        row = {}
        for col in model.__table__.columns:
            value = getattr(obj, col.name)
            row[col.name] = value.isoformat() if hasattr(value, "isoformat") else value
        rows.append(row)
    dump_csv(ROOT / "data" / "csv" / filename, rows)
    return rows


def generate(seed=SEED, scale=1.0):
    random.seed(seed)
    Faker.seed(seed)
    fake = Faker()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        counts = {
            "requisitions": max(1, int(100 * scale)),
            "candidates": max(1, int(2000 * scale)),
            "applications": max(1, int(3000 * scale)),
            "interviews": max(1, int(600 * scale)),
            "offers": max(1, int(150 * scale)),
        }

        # 1. Master data: departments and skills.
        departments = []
        for i, name in enumerate(DEPARTMENTS, 1):
            obj = Department(name=name, cost_center=f"CC-{i:03d}")
            db.add(obj)
            departments.append(obj)
        skill_objects = {}
        for name in SKILLS:
            obj = Skill(name=name)
            db.add(obj)
            skill_objects[name] = obj
        db.flush()

        # 2. Approved requisitions and their required skills/rules.
        requisitions = []
        for i in range(1, counts["requisitions"] + 1):
            dept = random.choice(departments)
            min_sal = random.randrange(500000, 1200000, 50000)
            max_sal = min_sal + random.randrange(300000, 900000, 50000)
            req = JobRequisition(
                id=f"REQ-2026-{i:06d}", department_id=dept.id,
                title=random.choice(TITLES), location=random.choice(CITIES),
                employment_type=random.choice(["FULL_TIME", "CONTRACT"]),
                status="OPEN", min_salary=float(min_sal), max_salary=float(max_sal),
                approved_by=f"Approver {random.randint(1, 12)}",
                approved_at=datetime(2026, 9, 1) + timedelta(days=random.randrange(25)),
                created_at=datetime(2026, 8, 1) + timedelta(days=random.randrange(25))
            )
            db.add(req)
            requisitions.append(req)
        db.flush()

        for req in requisitions:
            required = random.sample(SKILLS, k=random.randint(3, 6))
            for skill_name in required:
                db.add(RequisitionSkill(
                    requisition_id=req.id, skill_id=skill_objects[skill_name].id,
                    importance=round(random.uniform(0.7, 1.5), 2)
                ))
            db.add(ScreeningRule(
                requisition_id=req.id, min_experience=random.choice([0, 1, 2, 3, 5]),
                minimum_score=60.0, skill_weight=0.75, experience_weight=0.25,
                effective_from=date(2026, 1, 1), effective_to=None
            ))

        # 3. Synthetic candidates and resume metadata.
        candidates = []
        for i in range(1, counts["candidates"] + 1):
            candidate = Candidate(
                id=f"CAND-{i:06d}", full_name=fake.name(),
                email=f"candidate{i:06d}@example.test",
                city=random.choice(CITIES),
                years_experience=round(random.uniform(0, 12), 1),
                created_at=datetime(2026, 9, 1) + timedelta(days=random.randrange(50))
            )
            db.add(candidate)
            candidates.append(candidate)
        db.flush()

        for candidate in candidates:
            for skill_name in random.sample(SKILLS, k=random.randint(2, 9)):
                db.add(CandidateSkill(
                    candidate_id=candidate.id, skill_id=skill_objects[skill_name].id,
                    proficiency=random.choice(["BEGINNER", "INTERMEDIATE", "ADVANCED"]),
                    years_used=round(random.uniform(0, max(0.1, candidate.years_experience)), 1)
                ))
            db.add(ResumeArtifact(
                id=f"RES-{candidate.id}", candidate_id=candidate.id,
                file_name=f"{candidate.id}_resume.pdf", file_type="PDF",
                file_size_kb=random.randint(80, 900),
                parsed_at=datetime(2026, 9, 10), source="SYNTHETIC"
            ))
        db.flush()

        # Interviewers with a simple synthetic department assignment.
        interviewers = []
        for i in range(1, 61):
            obj = Interviewer(
                id=f"IVR-{i:04d}", full_name=fake.name(),
                department_id=random.choice(departments).id, active=True
            )
            db.add(obj)
            interviewers.append(obj)
        db.flush()

        # 4. Applications linked to valid requisitions/candidates.
        applications = []
        used_pairs = set()
        for i in range(1, counts["applications"] + 1):
            req = random.choice(requisitions)
            candidate = random.choice(candidates)
            pair = (req.id, candidate.id)
            duplicate = pair in used_pairs
            used_pairs.add(pair)
            app_id = f"APP-{req.id}-{candidate.id}"
            # A deliberate duplicate is represented as a separate application row
            # with a deterministic suffix to preserve primary-key uniqueness.
            if duplicate:
                app_id += f"-DUP-{i:06d}"
            req_skill_rows = db.query(RequisitionSkill).filter_by(requisition_id=req.id).all()
            names = [x.skill.name for x in candidate.skills]
            rule = db.query(ScreeningRule).filter_by(requisition_id=req.id).first()
            score, decision, matched, missing = score_candidate(
                candidate, req_skill_rows, names, rule
            )
            stage = random.choices(STAGES, weights=[15, 18, 25, 18, 8, 10, 6])[0]
            status = "WITHDRAWN" if stage == "WITHDRAWN" else (
                "CLOSED" if stage in ["REJECTED", "HIRED"] else "ACTIVE"
            )
            app = Application(
                id=app_id, requisition_id=req.id, candidate_id=candidate.id,
                applied_at=datetime(2026, 9, 1) + timedelta(days=random.randrange(55)),
                stage=stage, status=status, screening_score=score,
                duplicate_flag=duplicate
            )
            db.add(app)
            applications.append(app)
            db.add(ApplicationEvent(
                application_id=app_id, from_stage=None, to_stage="APPLIED",
                event_type="APPLICATION_CREATED", event_at=datetime(2026, 9, 1),
                actor="SYSTEM", note="Synthetic application created"
            ))
            if stage != "APPLIED":
                db.add(ApplicationEvent(
                    application_id=app_id, from_stage="APPLIED", to_stage=stage,
                    event_type="SYNTHETIC_INITIAL_STATE", event_at=datetime(2026, 9, 2),
                    actor="SYSTEM", note="Initial generated lifecycle state"
                ))
        db.flush()

        # 5. Interviews. Each interviewer gets a deterministic weekly calendar.
        eligible_apps = [a for a in applications if a.stage in ["INTERVIEW", "OFFER", "HIRED"]]
        if not eligible_apps:
            eligible_apps = applications
        interview_rows = []
        for i in range(1, counts["interviews"] + 1):
            app = random.choice(eligible_apps)
            interviewer = random.choice(interviewers)
            day = datetime(2026, 10, 1) + timedelta(days=random.randrange(28))
            start = day.replace(hour=random.choice([9, 10, 11, 13, 14, 15]), minute=0)
            end = start + timedelta(minutes=60)
            conflict = random.random() < 0.04
            if conflict:
                # Force overlap with a prior interview for the same interviewer.
                prior = next((x for x in interview_rows if x.interviewer_id == interviewer.id), None)
                if prior:
                    start = prior.scheduled_start + timedelta(minutes=15)
                    end = start + timedelta(minutes=60)
                else:
                    conflict = False
            interview = Interview(
                id=f"INT-2026-{i:06d}", application_id=app.id,
                interviewer_id=interviewer.id, round_number=random.choice([1, 2, 3]),
                scheduled_start=start, scheduled_end=end,
                status="SCHEDULED", conflict_flag=conflict
            )
            db.add(interview)
            interview_rows.append(interview)
        db.flush()

        # 6. Feedback: most completed interviews receive structured feedback.
        for interview in interview_rows:
            if random.random() < 0.78:
                ivr = interview.interviewer_id
                db.add(Feedback(
                    id=f"FB-{interview.id}-{ivr}", interview_id=interview.id,
                    interviewer_id=ivr, technical_score=random.randint(1, 5),
                    communication_score=random.randint(1, 5),
                    problem_solving_score=random.randint(1, 5),
                    recommendation=random.choice(["STRONG_YES", "YES", "MAYBE", "NO"]),
                    comments="Synthetic structured interview feedback.",
                    submitted_at=interview.scheduled_end + timedelta(hours=2)
                ))

        # 7. Offers: normal records stay within approved salary bands.
        offer_apps = [a for a in applications if a.stage in ["OFFER", "HIRED"]]
        if not offer_apps:
            offer_apps = applications
        offer_apps = offer_apps[:counts["offers"]]
        for i, app in enumerate(offer_apps, 1):
            req = app.requisition
            salary = random.uniform(req.min_salary, req.max_salary)
            status = random.choice(["PENDING", "ACCEPTED", "REJECTED"])
            db.add(Offer(
                id=f"OFF-2026-{i:06d}", application_id=app.id,
                salary=round(salary, 2), status=status,
                approved_by=f"Compensation Approver {random.randint(1, 8)}",
                approved_at=datetime(2026, 10, 10),
                issued_at=datetime(2026, 10, 11),
                response_at=datetime(2026, 10, 15) if status != "PENDING" else None
            ))
        db.flush()

        # 8. Explicit labelled anomaly injection. Keep labels out of feature tables.
        truth = []
        def label(issue_type, record_id, expected, details):
            truth.append({
                "issue_type": issue_type, "record_id": record_id,
                "ground_truth": expected, "details": details
            })

        # Unavailable interviewer: force a new overlapping interview record.
        if interview_rows:
            first = interview_rows[0]
            anomaly = Interview(
                id="INT-2026-ANOM-0001", application_id=first.application_id,
                interviewer_id=first.interviewer_id, round_number=3,
                scheduled_start=first.scheduled_start + timedelta(minutes=15),
                scheduled_end=first.scheduled_end + timedelta(minutes=75),
                status="SCHEDULED", conflict_flag=True
            )
            db.add(anomaly)
            label("INTERVIEWER_UNAVAILABLE", anomaly.id, "FLAG_CONFLICT",
                  "Interview overlaps an existing booking for the same interviewer.")

        # Duplicate candidate/requisition application pair already exists by design;
        # if none was drawn naturally, add a duplicate application with unique PK.
        duplicate_app = next((a for a in applications if a.duplicate_flag), None)
        if duplicate_app:
            label("DUPLICATE_APPLICATION", duplicate_app.id, "FLAG_DUPLICATE",
                  "Candidate has more than one application to the same requisition.")
        else:
            base = applications[0]
            duplicate_id = base.id + "-DUP-EDGE"
            db.add(Application(
                id=duplicate_id, requisition_id=base.requisition_id,
                candidate_id=base.candidate_id, applied_at=base.applied_at + timedelta(days=1),
                stage="APPLIED", status="ACTIVE", screening_score=base.screening_score,
                duplicate_flag=True
            ))
            label("DUPLICATE_APPLICATION", duplicate_id, "FLAG_DUPLICATE",
                  "Injected duplicate candidate/requisition pair.")

        # Missing feedback but stage advanced: interview with no feedback, label it.
        interview_with_no_feedback = interview_rows[0] if interview_rows else None
        if interview_with_no_feedback:
            # Ensure the exception exists deterministically, regardless of random feedback draw.
            db.query(Feedback).filter_by(interview_id=interview_with_no_feedback.id).delete()
            app = interview_with_no_feedback.application
            app.stage = "INTERVIEW"
            app.status = "ACTIVE"
            label("MISSING_FEEDBACK_STAGE_ADVANCED", app.id, "FLAG_MISSING_FEEDBACK",
                  f"Interview {interview_with_no_feedback.id} has no feedback but application reached interview stage.")

        # Salary outside approved band: create deliberately invalid offer.
        edge_app = applications[0]
        req = edge_app.requisition
        edge_offer = Offer(
            id="OFF-2026-ANOM-0001", application_id=edge_app.id,
            salary=round(req.max_salary + 250000, 2), status="PENDING",
            approved_by="Unapproved Exception", approved_at=datetime(2026, 10, 20),
            issued_at=datetime(2026, 10, 21)
        )
        db.add(edge_offer)
        label("OFFER_OUTSIDE_APPROVED_BAND", edge_offer.id, "BLOCK_OFFER",
              "Offer salary exceeds requisition maximum approved salary.")

        # Closed requisition with active applications.
        closed_req = requisitions[0]
        closed_req.status = "CLOSED"
        active_app = next((a for a in applications
                           if a.requisition_id == closed_req.id and a.status == "ACTIVE"), None)
        if active_app is None:
            active_app = next((a for a in applications if a.requisition_id == closed_req.id), None)
            if active_app:
                active_app.status = "ACTIVE"
                active_app.stage = "SCREENING"
        if active_app:
            label("CLOSED_ROLE_ACTIVE_APPLICATIONS", closed_req.id, "FLAG_LIFECYCLE",
                  f"Closed requisition still has active application {active_app.id}.")
        else:
            label("CLOSED_ROLE_ACTIVE_APPLICATIONS", closed_req.id, "FLAG_LIFECYCLE",
                  "Closed requisition has no application in this scaled sample.")

        db.commit()

        # 9. Export all entity tables.
        model_files = [
            (Department, "departments.csv"), (JobRequisition, "job_requisitions.csv"),
            (Candidate, "candidates.csv"), (Skill, "skills.csv"),
            (RequisitionSkill, "requisition_skills.csv"),
            (CandidateSkill, "candidate_skills.csv"),
            (ResumeArtifact, "resume_artifacts.csv"),
            (ScreeningRule, "screening_rules.csv"), (Application, "applications.csv"),
            (Interviewer, "interviewers.csv"), (Interview, "interviews.csv"),
            (Feedback, "feedback.csv"), (Offer, "offers.csv"),
            (ApplicationEvent, "application_events.csv")
        ]
        exported = {}
        for model, filename in model_files:
            exported[filename] = export_table(db, model, filename)

        (ROOT / "data" / "json").mkdir(parents=True, exist_ok=True)
        (ROOT / "data" / "json" / "ground_truth.json").write_text(
            json.dumps(truth, indent=2), encoding="utf-8"
        )
        dump_csv(ROOT / "data" / "ground_truth" / "ground_truth.csv", truth)

        # SQL schema + INSERT seed export from the same generated records.
        sql_path = ROOT / "data" / "sql" / "hireflow_seed.sql"
        with engine.connect() as conn:
            result = conn.exec_driver_sql(
                "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        sql_parts = ["-- HireFlow AI schema and synthetic seed data\n"]
        sql_parts.extend((row[1] or "") + ";\n" for row in result)
        for model, filename in model_files:
            rows = exported[filename]
            if not rows:
                continue
            columns = list(rows[0].keys())
            for row in rows:
                values = []
                for column in columns:
                    value = row[column]
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, bool):
                        values.append("1" if value else "0")
                    elif isinstance(value, (int, float)):
                        values.append(str(value))
                    else:
                        values.append("'" + str(value).replace("'", "''") + "'")
                sql_parts.append(
                    f"INSERT INTO {model.__tablename__} ({', '.join(columns)}) VALUES ({', '.join(values)});\n"
                )
        sql_path.write_text("".join(sql_parts), encoding="utf-8")

        # 10. Reproducibility manifest/checksum for generated CSV outputs.
        manifest = {
            "seed": seed, "scale": scale, "counts_requested": counts,
            "counts_actual": {name: len(rows) for name, rows in exported.items()},
            "ground_truth_rows": len(truth),
            "files": {}
        }
        for path in sorted((ROOT / "data").rglob("*.csv")):
            manifest["files"][str(path.relative_to(ROOT))] = hashlib.sha256(
                path.read_bytes()).hexdigest()
        (ROOT / "data" / "source_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        validation = {
            "primary_key_policy": "SQLAlchemy primary keys enforced by SQLite",
            "foreign_key_policy": "Foreign keys declared in SQLAlchemy models",
            "seed": seed, "scale": scale,
            "row_counts": manifest["counts_actual"],
            "labelled_edge_cases": truth,
            "notes": [
                "All candidate data is synthetic and uses example.test email addresses.",
                "Ground truth is exported separately and must not be used as a model input.",
                "Deliberate anomaly records are labelled; normal records are generated first."
            ]
        }
        (ROOT / "docs" / "validation_summary.json").write_text(
            json.dumps(validation, indent=2), encoding="utf-8"
        )
        print(json.dumps(manifest, indent=2))
        print("\nGeneration completed.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--scale", type=float, default=1.0)
    args = parser.parse_args()
    if args.scale <= 0 or args.scale > 1:
        raise SystemExit("--scale must be > 0 and <= 1")
    generate(args.seed, args.scale)
