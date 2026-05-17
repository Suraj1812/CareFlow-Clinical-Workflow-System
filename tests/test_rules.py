from app.rules.engine import evaluate_missed_schedules, evaluate_observation


def test_blood_sugar_rule_is_deterministic():
    first = evaluate_observation("blood_sugar", 320)
    second = evaluate_observation("blood_sugar", 320)

    assert first == second
    assert first[0].severity == "HIGH"
    assert first[0].rule_id == "blood_sugar_gt_300"


def test_heart_rate_rule_threshold():
    assert evaluate_observation("heart_rate", 121)[0].severity == "HIGH"
    assert evaluate_observation("heart_rate", 120) == []


def test_missed_schedule_rule():
    assert evaluate_missed_schedules(2) == []
    assert evaluate_missed_schedules(3)[0].severity == "MEDIUM"

