from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:12].upper()}"


def new_patient_id() -> str:
    return f"P{uuid4().hex[:8].upper()}"
