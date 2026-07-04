import json
import tempfile
from pathlib import Path

from cirecon.memory import (
    FixRecord,
    MemoryContext,
    load_memory,
    record_fix,
    record_rejected_fix,
    save_memory,
    update_pr_status,
    was_fix_rejected,
)


def test_save_and_load_roundtrip():
    ctx = MemoryContext(
        repo="test/repo",
        total_runs=3,
        fixes=[
            FixRecord(
                issue_id="RULE_001",
                file=".github/workflows/ci.yml",
                fix_applied="bump actions/checkout@v2 -> v4",
                pr_url="https://github.com/test/repo/pull/1",
                pr_status="open",
            )
        ],
        rejected_fixes=["RULE_002"],
        known_secrets=["MY_SECRET"],
    )
    with tempfile.TemporaryDirectory() as tmp:
        save_memory(ctx, tmp)
        loaded = load_memory(tmp)

    assert loaded.repo == "test/repo"
    assert loaded.total_runs == 3
    assert len(loaded.fixes) == 1
    assert loaded.fixes[0].issue_id == "RULE_001"
    assert loaded.fixes[0].pr_url == "https://github.com/test/repo/pull/1"
    assert loaded.fixes[0].pr_status == "open"
    assert loaded.rejected_fixes == ["RULE_002"]
    assert loaded.known_secrets == ["MY_SECRET"]


def test_load_missing_file_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        ctx = load_memory(tmp)
    assert ctx.total_runs == 0
    assert ctx.fixes == []
    assert ctx.rejected_fixes == []


def test_save_creates_directory():
    with tempfile.TemporaryDirectory() as tmp:
        ctx = MemoryContext(repo="test/repo")
        save_memory(ctx, tmp)
        mem_file = Path(tmp) / ".github" / "cirecon" / "memory.json"
        assert mem_file.exists()
        raw = json.loads(mem_file.read_text())
        assert raw["repo"] == "test/repo"


def test_record_fix_appends():
    ctx = MemoryContext(repo="test/repo")
    fix = FixRecord(
        issue_id="RULE_001",
        file="f.yml",
        fix_applied="bump v2->v4",
        pr_url="https://github.com/test/repo/pull/1",
        pr_status="open",
    )
    record_fix(ctx, fix)
    assert len(ctx.fixes) == 1
    assert ctx.fixes[0].issue_id == "RULE_001"


def test_record_rejected_fix_deduplicates():
    ctx = MemoryContext(repo="test/repo")
    record_rejected_fix(ctx, "RULE_BAD")
    record_rejected_fix(ctx, "RULE_BAD")
    assert ctx.rejected_fixes == ["RULE_BAD"]


def test_update_pr_status_to_merged():
    ctx = MemoryContext(repo="test/repo")
    fix = FixRecord(
        issue_id="RULE_001",
        file="f.yml",
        fix_applied="bump",
        pr_url="https://github.com/test/repo/pull/1",
        pr_status="open",
    )
    record_fix(ctx, fix)
    update_pr_status(ctx, "https://github.com/test/repo/pull/1", "merged")
    assert ctx.fixes[0].pr_status == "merged"
    assert "RULE_001" not in ctx.rejected_fixes


def test_update_pr_status_to_closed_adds_rejected():
    ctx = MemoryContext(repo="test/repo")
    fix = FixRecord(
        issue_id="RULE_001",
        file="f.yml",
        fix_applied="bump",
        pr_url="https://github.com/test/repo/pull/1",
        pr_status="open",
    )
    record_fix(ctx, fix)
    update_pr_status(ctx, "https://github.com/test/repo/pull/1", "closed")
    assert ctx.fixes[0].pr_status == "closed"
    assert "RULE_001" in ctx.rejected_fixes


def test_was_fix_rejected():
    ctx = MemoryContext(repo="test/repo")
    record_rejected_fix(ctx, "RULE_BAD")
    assert was_fix_rejected(ctx, "RULE_BAD") is True
    assert was_fix_rejected(ctx, "RULE_GOOD") is False
