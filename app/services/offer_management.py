def validate_offer_salary(requisition, salary):
    if salary < requisition.min_salary or salary > requisition.max_salary:
        return False, (
            f"Salary {salary:.2f} is outside approved band "
            f"{requisition.min_salary:.2f}-{requisition.max_salary:.2f}"
        )
    return True, "Salary is within approved band"
