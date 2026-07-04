from cirecon.validator import validate_yaml_syntax


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
