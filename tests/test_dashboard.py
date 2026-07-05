from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from cirecon.dashboard import generate_dashboard_markdown, publish_to_gist
from cirecon.org_scanner import RepoReport
from cirecon.rule_engine import Issue, Location, Severity


def test_generate_dashboard_markdown_empty():
    md = generate_dashboard_markdown([])
    assert "# CIRecon Org Health Dashboard" in md
    assert "No repos scanned" in md


def test_generate_dashboard_markdown_clean():
    reports = [
        RepoReport(repo="owner/repo1", files_scanned=2, issues=[],
                   health_score=100,
                   scanned_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
        RepoReport(repo="owner/repo2", files_scanned=1, issues=[],
                   health_score=100,
                   scanned_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
    ]
    md = generate_dashboard_markdown(reports)
    assert "✅ Clean" in md
    assert "100/100" in md
    assert "Clean repos" in md


def test_generate_dashboard_markdown_with_issues():
    issues = [
        Issue(id="R1", severity=Severity.CRITICAL, message="bad",
              location=Location(file="f.yml", line=1, column=1),
              auto_fixable=False, confidence=1.0, suggested_fix=None),
    ]
    reports = [
        RepoReport(repo="owner/repo1", files_scanned=1, issues=issues,
                   health_score=80,
                   scanned_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
    ]
    md = generate_dashboard_markdown(reports)
    assert "80/100" in md
    assert "R1" in md
    assert "CRITICAL" in md
    assert "Manual fix required" in md


def test_generate_dashboard_markdown_with_fix():
    issues = [
        Issue(id="R2", severity=Severity.MEDIUM, message="old",
              location=Location(file="ci.yml", line=2, column=1),
              auto_fixable=True, confidence=1.0,
              suggested_fix="actions/checkout@v4"),
    ]
    reports = [
        RepoReport(repo="owner/repo1", files_scanned=1, issues=issues,
                   health_score=90,
                   scanned_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
    ]
    md = generate_dashboard_markdown(reports)
    assert "`actions/checkout@v4`" in md


@patch("cirecon.dashboard.requests.post")
def test_publish_to_gist_creates(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"html_url": "https://gist.github.com/abc123"}
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    url = publish_to_gist("# Dashboard", "ghp_token")
    assert url == "https://gist.github.com/abc123"
    mock_post.assert_called_once()


@patch("cirecon.dashboard.requests.patch")
def test_publish_to_gist_updates(mock_patch):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"html_url": "https://gist.github.com/existing"}
    mock_resp.raise_for_status.return_value = None
    mock_patch.return_value = mock_resp

    url = publish_to_gist("# Dashboard", "ghp_token", gist_id="existing")
    assert url == "https://gist.github.com/existing"
    mock_patch.assert_called_once()
