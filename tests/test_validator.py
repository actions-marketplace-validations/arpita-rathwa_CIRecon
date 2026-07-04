from unittest.mock import patch

import jsonschema
import yaml

from cirecon.validator import (
    fetch_github_actions_schema,
    validate_schema,
    validate_yaml_syntax,
)

MINIMAL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "on": {},
        "jobs": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "properties": {
                        "runs-on": {"type": "string"},
                        "steps": {"type": "array"},
                    },
                }
            },
        },
    },
    "required": ["on", "jobs"],
}


def test_valid_yaml_passes():
    content = "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest"
    result = validate_yaml_syntax(content)
    assert result.passed is True
    assert result.errors == []


def test_broken_yaml_fails():
    content = "name: CI\non: [push\njobs:\n  build:\n    runs-on: ubuntu-latest"
    result = validate_yaml_syntax(content)
    assert result.passed is False
    assert len(result.errors) > 0


@patch("cirecon.validator._SCHEMA_CACHE", MINIMAL_SCHEMA)
def test_schema_valid_workflow_passes():
    content = "name: CI\n'on': [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hello\n"
    result = validate_schema(content)
    assert result.passed is True
    assert result.errors == []


@patch("cirecon.validator._SCHEMA_CACHE", MINIMAL_SCHEMA)
def test_schema_missing_on_fails():
    content = "name: CI\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hello\n"
    result = validate_schema(content)
    assert result.passed is False
    assert len(result.errors) > 0
