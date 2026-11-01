def score_candidate(candidate, required_skill_rows, candidate_skill_names, rule):
    """Score only job-related criteria: required skills and relevant experience."""
    required = {row.skill.name: row.importance for row in required_skill_rows}
    available = set(candidate_skill_names)
    matched = sorted(required.keys() & available)
    missing = sorted(required.keys() - available)

    total_weight = sum(required.values()) or 1
    skill_score = sum(required[name] for name in matched) / total_weight * 100

    if rule.min_experience <= 0:
        experience_score = 100.0
    else:
        experience_score = min(candidate.years_experience / rule.min_experience, 1.0) * 100

    score = (
        skill_score * rule.skill_weight
        + experience_score * rule.experience_weight
    )
    decision = "PASS" if score >= rule.minimum_score else "REVIEW"
    return round(score, 2), decision, matched, missing
