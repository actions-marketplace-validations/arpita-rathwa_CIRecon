from dataclasses import dataclass
from typing import Optional

import jsonschema
import requests
import yaml


_SCHEMA_CACHE: Optional[dict] = None


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


def fetch_github_actions_schema() -> dict:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE
    resp = requests.get("https://json.schemastore.org/github-workflow.json", timeout=30)
    resp.raise_for_status()
    _SCHEMA_CACHE = resp.json()
    return _SCHEMA_CACHE


def validate_schema(content: str) -> ValidationResult:
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return ValidationResult(passed=False, errors=[f"YAML parse error: {e}"])
    if parsed is None:
        return ValidationResult(passed=False, errors=["Empty YAML content"])
    try:
        schema = fetch_github_actions_schema()
        jsonschema.validate(parsed, schema)
        return ValidationResult(passed=True, errors=[])
    except jsonschema.ValidationError as e:
        return ValidationResult(passed=False, errors=[e.message])
    except requests.RequestException as e:
        return ValidationResult(passed=False, errors=[f"Schema fetch error: {e}"])