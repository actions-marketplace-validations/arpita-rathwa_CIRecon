import pytest
from cirecon.rule_engine import (
    check_deprecated_action_versions,
    Severity
)


def load_fixture(filename: str) -> str:
    with open(f"tests/fixtures/{filename}", "r") as f:
        return f.read()


def test_detects_deprecated_action_versions():
    content = load_fixture("deprecated_action.yml")
    issues = check_deprecated_action_versions("deprecated_action.yml", content)

    assert len(issues) == 2

    ids = [i.id for i in issues]
    assert ids.count("RULE_DEPRECATED_ACTION") == 2

    fixes = [i.suggested_fix for i in issues]
    assert "actions/checkout@v4" in fixes
    assert "actions/setup-python@v5" in fixes


def test_no_issues_on_clean_file():
    content = """
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
"""
    issues = check_deprecated_action_versions("clean.yml", content)
    assert len(issues) == 0