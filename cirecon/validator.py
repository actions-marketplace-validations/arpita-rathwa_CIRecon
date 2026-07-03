from dataclasses import dataclass


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str]