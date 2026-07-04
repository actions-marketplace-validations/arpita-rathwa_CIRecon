import tempfile
from pathlib import Path

from cirecon.fix_applier import apply_fix
from cirecon.input_layer import discover_workflow_files
from cirecon.rule_engine import run_all_checks
from cirecon.validator import validate_all

BROKEN_FIXTURE = """\
name: CI
'on': [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v4
"""


def test_full_pipeline_on_broken_fixture():
    with tempfile.TemporaryDirectory() as tmp:
        workflows_dir = Path(tmp) / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        fixture_path = workflows_dir / "ci.yml"
        fixture_path.write_text(BROKEN_FIXTURE, encoding="utf-8")

        files = discover_workflow_files(tmp)
        assert len(files) == 1

        path, content = files[0]
        issues = run_all_checks(path, content)
        assert len(issues) >= 1
        ids = [i.id for i in issues]
        assert "RULE_DEPRECATED_ACTION" in ids
        assert "RULE_DEPRECATED_ACTION" == issues[0].id

        for issue in issues:
            if issue.auto_fixable:
                content = apply_fix(content, issue)

        result = validate_all(path, content, issues)
        assert result.passed is True, f"Validation failed: {result.errors}"

        assert "actions/checkout@v4" in content
        assert "actions/checkout@v2" not in content
        assert "actions/setup-python@v5" in content
        assert "actions/setup-python@v4" not in content
        assert "permissions:" in content
