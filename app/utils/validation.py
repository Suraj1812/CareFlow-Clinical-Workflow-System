from datetime import datetime


def parse_hhmm(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValueError("time must be in HH:MM 24-hour format") from exc
    return parsed.strftime("%H:%M")

