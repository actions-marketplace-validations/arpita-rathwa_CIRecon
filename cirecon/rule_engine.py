from dataclasses import dataclass
from typing import Optional
from enum import Enum


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Location:
    file: str
    line: Optional[int]
    column: Optional[int]


@dataclass
class Issue:
    id: str
    severity: Severity
    message: str
    location: Location
    auto_fixable: bool
    confidence: float        # 0.0 to 1.0
    suggested_fix: Optional[str]

import re
import yaml


# Deprecated action versions that should be bumped
DEPRECATED_ACTIONS = {
    "actions/checkout": "v4",
    "actions/setup-python": "v5",
    "actions/setup-node": "v4",
    "actions/upload-artifact": "v4",
    "actions/download-artifact": "v4",
    "actions/cache": "v4",
}


def check_deprecated_action_versions(path: str, content: str) -> list[Issue]:
    issues = []

    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError:
        return issues  # syntax errors handled by a separate rule

    if not parsed or "jobs" not in parsed:
        return issues

    for job_name, job in parsed["jobs"].items():
        steps = job.get("steps", [])
        for step_index, step in enumerate(steps):
            uses = step.get("uses", "")
            if not uses:
                continue

            # split "actions/checkout@v2" into "actions/checkout" and "v2"
            if "@" not in uses:
                continue

            action, version = uses.rsplit("@", 1)

            if action in DEPRECATED_ACTIONS:
                latest = DEPRECATED_ACTIONS[action]
                if version != latest:
                    issues.append(Issue(
                        id="RULE_DEPRECATED_ACTION",
                        severity=Severity.MEDIUM,
                        message=f"'{action}@{version}' is outdated. Latest is '@{latest}'.",
                        location=Location(file=path, line=None, column=None),
                        auto_fixable=True,
                        confidence=1.0,
                        suggested_fix=f"{action}@{latest}"
                    ))

    return issues