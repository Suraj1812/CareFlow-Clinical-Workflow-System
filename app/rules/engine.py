from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    severity: str
    reason: str
    rule_id: str


def evaluate_observation(observation_type: str, value: float) -> list[RuleResult]:
    results: list[RuleResult] = []

    if observation_type == "blood_sugar" and value > 300:
        results.append(
            RuleResult(
                severity="HIGH",
                reason=f"Blood sugar reading {value:g} exceeds threshold 300.",
                rule_id="blood_sugar_gt_300",
            )
        )

    if observation_type == "heart_rate" and value > 120:
        results.append(
            RuleResult(
                severity="HIGH",
                reason=f"Heart rate reading {value:g} exceeds threshold 120.",
                rule_id="heart_rate_gt_120",
            )
        )

    return results


def evaluate_missed_schedules(missed_count: int) -> list[RuleResult]:
    if missed_count >= 3:
        return [
            RuleResult(
                severity="MEDIUM",
                reason=f"Patient has {missed_count} missed schedules.",
                rule_id="missed_schedules_gte_3",
            )
        ]
    return []

