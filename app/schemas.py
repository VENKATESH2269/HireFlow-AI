from pydantic import BaseModel, Field


class ScreeningResult(BaseModel):
    application_id: str
    score: float = Field(ge=0, le=100)
    decision: str
    matched_skills: list[str]
    missing_skills: list[str]


class OfferDecision(BaseModel):
    application_id: str
    salary: float = Field(gt=0)
    approved_by: str = Field(min_length=2)
