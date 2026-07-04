from dataclasses import dataclass

import yaml


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str]


def validate_yaml_syntax(content: str) -> ValidationResult:
    try:
        yaml.safe_load(content)
        return ValidationResult(passed=True, errors=[])
    except yaml.YAMLError as e:
        return ValidationResult(passed=False, errors=[str(e)])