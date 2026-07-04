import sys
from unittest.mock import patch, MagicMock

import pytest

from cirecon.main import _issue_to_dict, run
from cirecon.rule_engine import Issue, Location, Severity


def test_issue_to_dict():
    issue = Issue(
        id="RULE_TEST",
        severity=Severity.HIGH,
        message="Test issue",
        location=Location(file="f.yml", line=5, column=2),
        auto_fixable=True,
        confidence=1.0,
        suggested_fix="fix",
    )
    d = _issue_to_dict(issue)
    assert d["id"] == "RULE_TEST"
    assert d["severity"] == "high"
    assert d["auto_fixable"] is True
    assert d["location"]["file"] == "f.yml"


@patch("cirecon.main.discover_workflow_files")
@patch("cirecon.main.run_all_checks")
def test_run_no_issues_found(mock_checks, mock_discover):
    mock_discover.return_value = [("test.yml", "name: CI")]
    mock_checks.return_value = []

    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 0


@patch("cirecon.main.discover_workflow_files")
@patch("cirecon.main.run_all_checks")
@patch("cirecon.main.apply_fix")
@patch("cirecon.main.validate_all")
def test_run_auto_fix_applied(mock_validate, mock_apply, mock_checks, mock_discover):
    mock_discover.return_value = [("test.yml", "name: CI\njobs:\n  build:\n    steps:\n      - uses: actions/checkout@v2\n")]
    mock_checks.return_value = [
        Issue(
            id="RULE_DEPRECATED_ACTION",
            severity=Severity.MEDIUM,
            message="'actions/checkout@v2' is outdated",
            location=Location(file="test.yml", line=None, column=None),
            auto_fixable=True,
            confidence=1.0,
            suggested_fix="actions/checkout@v4",
        )
    ]
    mock_apply.return_value = "name: CI\njobs:\n  build:\n    steps:\n      - uses: actions/checkout@v4\n"

    valid_result = MagicMock()
    valid_result.passed = True
    valid_result.errors = []
    mock_validate.return_value = valid_result

    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 0


@patch("cirecon.main.discover_workflow_files")
@patch("cirecon.main.run_all_checks")
@patch("cirecon.main.apply_fix")
@patch("cirecon.main.validate_all")
def test_run_auto_fix_fails_validation(mock_validate, mock_apply, mock_checks, mock_discover):
    mock_discover.return_value = [("test.yml", "bad yaml")]
    mock_checks.return_value = [
        Issue(
            id="RULE_MISSING_PERMISSIONS_BLOCK",
            severity=Severity.HIGH,
            message="Missing permissions",
            location=Location(file="test.yml", line=None, column=None),
            auto_fixable=True,
            confidence=0.9,
            suggested_fix="permissions:\n  contents: read",
        )
    ]
    mock_apply.return_value = "still bad"

    failed_result = MagicMock()
    failed_result.passed = False
    failed_result.errors = ["validation failed"]
    mock_validate.return_value = failed_result

    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 0


@patch("cirecon.main.discover_workflow_files")
def test_no_workflow_files(mock_discover):
    mock_discover.return_value = []
    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 0
