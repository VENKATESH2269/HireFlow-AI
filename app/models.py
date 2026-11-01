from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String,
    Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    cost_center = Column(String(30), nullable=False, unique=True)
    requisitions = relationship("JobRequisition", back_populates="department")


class JobRequisition(Base):
    __tablename__ = "job_requisitions"
    id = Column(String(30), primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    title = Column(String(120), nullable=False)
    location = Column(String(100), nullable=False)
    employment_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    min_salary = Column(Float, nullable=False)
    max_salary = Column(Float, nullable=False)
    approved_by = Column(String(100), nullable=False)
    approved_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    department = relationship("Department", back_populates="requisitions")
    required_skills = relationship("RequisitionSkill", back_populates="requisition")
    applications = relationship("Application", back_populates="requisition")


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(String(30), primary_key=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(180), nullable=False, unique=True)
    city = Column(String(100), nullable=False)
    years_experience = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    skills = relationship("CandidateSkill", back_populates="candidate")
    applications = relationship("Application", back_populates="candidate")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)


class RequisitionSkill(Base):
    __tablename__ = "requisition_skills"
    id = Column(Integer, primary_key=True)
    requisition_id = Column(String(30), ForeignKey("job_requisitions.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    importance = Column(Float, nullable=False, default=1.0)
    __table_args__ = (UniqueConstraint("requisition_id", "skill_id"),)
    requisition = relationship("JobRequisition", back_populates="required_skills")
    skill = relationship("Skill")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(String(30), ForeignKey("candidates.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    proficiency = Column(String(20), nullable=False)
    years_used = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id"),)
    candidate = relationship("Candidate", back_populates="skills")
    skill = relationship("Skill")


class ResumeArtifact(Base):
    __tablename__ = "resume_artifacts"
    id = Column(String(40), primary_key=True)
    candidate_id = Column(String(30), ForeignKey("candidates.id"), nullable=False, unique=True)
    file_name = Column(String(180), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size_kb = Column(Integer, nullable=False)
    parsed_at = Column(DateTime, nullable=True)
    source = Column(String(30), nullable=False, default="SYNTHETIC")
    candidate = relationship("Candidate")


class ScreeningRule(Base):
    __tablename__ = "screening_rules"
    id = Column(Integer, primary_key=True)
    requisition_id = Column(String(30), ForeignKey("job_requisitions.id"), nullable=False)
    min_experience = Column(Float, nullable=False)
    minimum_score = Column(Float, nullable=False)
    skill_weight = Column(Float, nullable=False)
    experience_weight = Column(Float, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)


class Application(Base):
    __tablename__ = "applications"
    id = Column(String(120), primary_key=True)
    requisition_id = Column(String(30), ForeignKey("job_requisitions.id"), nullable=False)
    candidate_id = Column(String(30), ForeignKey("candidates.id"), nullable=False)
    applied_at = Column(DateTime, nullable=False)
    stage = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)
    screening_score = Column(Float, nullable=False)
    duplicate_flag = Column(Boolean, nullable=False, default=False)
    requisition = relationship("JobRequisition", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    interviews = relationship("Interview", back_populates="application")
    offers = relationship("Offer", back_populates="application")


class Interviewer(Base):
    __tablename__ = "interviewers"
    id = Column(String(30), primary_key=True)
    full_name = Column(String(150), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    active = Column(Boolean, nullable=False, default=True)


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(String(30), primary_key=True)
    application_id = Column(String(120), ForeignKey("applications.id"), nullable=False)
    interviewer_id = Column(String(30), ForeignKey("interviewers.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)
    conflict_flag = Column(Boolean, nullable=False, default=False)
    application = relationship("Application", back_populates="interviews")
    interviewer = relationship("Interviewer")
    feedback = relationship("Feedback", back_populates="interview")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(String(100), primary_key=True)
    interview_id = Column(String(30), ForeignKey("interviews.id"), nullable=False)
    interviewer_id = Column(String(30), ForeignKey("interviewers.id"), nullable=False)
    technical_score = Column(Float, nullable=False)
    communication_score = Column(Float, nullable=False)
    problem_solving_score = Column(Float, nullable=False)
    recommendation = Column(String(20), nullable=False)
    comments = Column(Text, nullable=False)
    submitted_at = Column(DateTime, nullable=False)
    interview = relationship("Interview", back_populates="feedback")
    interviewer = relationship("Interviewer")


class Offer(Base):
    __tablename__ = "offers"
    id = Column(String(30), primary_key=True)
    application_id = Column(String(120), ForeignKey("applications.id"), nullable=False)
    salary = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    approved_by = Column(String(100), nullable=False)
    approved_at = Column(DateTime, nullable=False)
    issued_at = Column(DateTime, nullable=False)
    response_at = Column(DateTime, nullable=True)
    application = relationship("Application", back_populates="offers")


class ApplicationEvent(Base):
    """Append-only lifecycle history; never replace previous stage records."""
    __tablename__ = "application_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(String(120), ForeignKey("applications.id"), nullable=False)
    from_stage = Column(String(30), nullable=True)
    to_stage = Column(String(30), nullable=False)
    event_type = Column(String(40), nullable=False)
    event_at = Column(DateTime, nullable=False)
    actor = Column(String(100), nullable=False)
    note = Column(Text, nullable=True)
