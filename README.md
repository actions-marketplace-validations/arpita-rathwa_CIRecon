
# CIRecon

> Security-aware CI/CD linter for GitHub Actions — detects workflow misconfigurations, flags security vulnerabilities, and reports everything directly in your Actions UI with inline annotations.

[![CI](https://github.com/arpita-rathwa/CIRecon/actions/workflows/ci.yml/badge.svg)](https://github.com/arpita-rathwa/CIRecon/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Marketplace](https://img.shields.io/badge/GitHub-Marketplace-orange)](https://github.com/marketplace/actions/cirecon)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](https://github.com/arpita-rathwa/CIRecon)

---

## The problem

A misindented YAML block, a deprecated action version, a secret accidentally printed to logs, a `pull_request` workflow that silently fails on fork PRs — these are the kinds of issues that only surface at 2am when your pipeline breaks in production. CIRecon catches them before they cause damage.

---

## What it does

CIRecon runs automatically on every push. It scans every workflow file with a 10-rule engine covering correctness, security, and runtime behavioral gaps. Every issue is surfaced in two ways:

- **Inline annotations** — red and yellow underlines on the exact file and line in the GitHub Actions UI
- **Job Summary** — a structured report visible on every Actions run page with severity, suggested fix, and auto-fixable status

For issues that need reasoning beyond static analysis, an optional Claude-powered agent loop provides deeper diagnosis.

---

## Quickstart

```yaml
name: CIRecon

on:
  push:
    paths:
      - '.github/workflows/**'
  pull_request:
    paths:
      - '.github/workflows/**'

jobs:
  cirecon:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: arpita-rathwa/CIRecon@v1
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

> `anthropic-api-key` is optional. Without it, CIRecon runs the full 10-rule engine for free.

See [`examples/cirecon.yml`](examples/cirecon.yml) for more configuration options.

---

## What CIRecon checks

### Correctness

| Rule | Description | Severity | Auto-fixable |
|---|---|---|---|
| `RULE_DEPRECATED_ACTION` | Action pinned to an outdated version (e.g. `checkout@v2`). SHA-pinned actions are exempt. | MEDIUM | ✅ |
| `RULE_MISSING_PERMISSIONS_BLOCK` | No top-level `permissions:` block — `GITHUB_TOKEN` gets broad default access. | HIGH | ✅ |
| `RULE_BROKEN_NEEDS_DEPENDENCY` | A `needs:` entry references a job ID that does not exist. | HIGH | ❌ |

### Security

| Rule | Description | Severity |
|---|---|---|
| `RULE_SECRET_IN_RUN_COMMAND` | `${{ secrets.* }}` in a `run:` step — secret values appear in plain text in logs. | CRITICAL |
| `RULE_PULL_REQUEST_TARGET_UNSAFE` | `pull_request_target` + checkout of PR ref — known RCE vector giving untrusted code write access. | CRITICAL |
| `RULE_OVERLY_BROAD_PERMISSIONS` | `write-all` or 3+ write-level permission scopes — increases blast radius if workflow is compromised. | HIGH |
| `RULE_UNPINNED_THIRD_PARTY_ACTION` | Third-party action not pinned to a 40-char commit SHA — can be silently updated with malicious code. | HIGH |

### Runtime behavioral

| Rule | Description | Severity |
|---|---|---|
| `RULE_FORK_PR_SECRET_EXPOSURE` | Workflow triggered by `pull_request` uses secrets — secrets are unavailable on fork PRs and silently become empty strings. | HIGH |
| `RULE_WRITE_STEP_ON_FORK_TRIGGER` | Step requiring write permissions in a `pull_request` workflow — silently fails on fork PRs which use a read-only token. | HIGH |
| `RULE_REF_CONDITION_MISMATCH` | `if: github.ref == 'refs/heads/...'` in a workflow triggered by both `push` and `pull_request` — always false on PRs, step silently skips. | MEDIUM |

---

## Output

### Inline annotations

CIRecon prints GitHub workflow commands that render as inline annotations on the specific file and line:

```
::error file=.github/workflows/ci.yml,line=12,title=RULE_SECRET_IN_RUN_COMMAND::Job 'lint' prints secret to logs
::warning file=.github/workflows/ci.yml,line=8,title=RULE_DEPRECATED_ACTION::actions/checkout@v2 is outdated
```

CRITICAL and HIGH issues appear as **red error annotations**. MEDIUM and LOW appear as **yellow warnings**. These are visible on the Actions run page, in PR diff views, and in the Files changed tab.

### Job Summary

Every run writes a structured report to the Actions Summary tab:

```
## CIRecon Report

Files scanned: 2 | Issues found: 5 | Needs attention: 3

| File | Rule | Severity | Auto-fixable | Suggested Fix |
|---|---|---|---|---|
| ci.yml | RULE_SECRET_IN_RUN_COMMAND | CRITICAL | ❌ | Manual fix required |
| ci.yml | RULE_DEPRECATED_ACTION | MEDIUM | ✅ | actions/checkout@v4 |
| ci.yml | RULE_MISSING_PERMISSIONS_BLOCK | HIGH | ✅ | permissions: contents: read |
```

---

## Org-wide dashboard

Scan all your repos on a schedule and publish a health dashboard to a GitHub Gist:

```yaml
name: CIRecon Dashboard

on:
  schedule:
    - cron: '0 9 * * 1'
  workflow_dispatch:

jobs:
  dashboard:
    runs-on: ubuntu-latest
    steps:
      - uses: arpita-rathwa/CIRecon@v1
        with:
          mode: dashboard
          repos: 'owner/repo1,owner/repo2,owner/repo3'
          gist-id: ${{ vars.CIRECON_GIST_ID }}
```

Health scores start at 100 and deduct per issue (CRITICAL: −20, HIGH: −10, MEDIUM: −5, LOW: −2). The Gist updates automatically on each run.

---

## How it works

```
push event
    → load per-repo memory
    → rule engine scans all .github/workflows/*.yml (10 rules)
    → validated fixes identified
    → agent loop (Claude) reasons about remaining issues
    → inline annotations printed to stdout
    → Job Summary written to $GITHUB_STEP_SUMMARY
```

CIRecon is **deterministic-first** — the rule engine runs before any LLM call. Claude is invoked only when static analysis needs deeper reasoning. Per-repo memory at `.github/cirecon/memory.json` means CIRecon learns from past runs — it won't re-surface issues that were previously resolved.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design.

---

## Configuration

| Input | Description | Default |
|---|---|---|
| `anthropic-api-key` | Anthropic API key — enables Claude-powered agent loop | _(optional)_ |
| `claude-model` | Claude model for agent loop | `claude-haiku-4-5-20251001` |
| `max-iterations` | Maximum agent loop iterations | `10` |
| `fail-on-unresolved` | Exit code 1 if issues remain | `false` |
| `mode` | `scan` (default) or `dashboard` | `scan` |
| `repos` | Comma-separated repos for dashboard mode | _(required in dashboard mode)_ |
| `gist-id` | Existing Gist ID to update in dashboard mode | _(optional)_ |

---

## Why not just use actionlint?

| Feature | actionlint | CIRecon |
|---|---|---|
| Syntax and schema validation | ✅ | ✅ |
| Security misconfiguration detection | ❌ | ✅ |
| Runtime behavioral gap detection | ❌ | ✅ |
| Inline annotations in GitHub UI | ❌ | ✅ |
| Job Summary report | ❌ | ✅ |
| Claude-powered agent reasoning | ❌ | ✅ |
| Per-repo memory | ❌ | ✅ |
| Org-wide health dashboard | ❌ | ✅ |
| Free to use | ✅ | ✅ |

---

## Contributing

Adding a new rule takes about 15 minutes. See [CONTRIBUTING.md](CONTRIBUTING.md) for a step-by-step guide.

Found a bug? Open an issue using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

---

## License

MIT — see [LICENSE](LICENSE).

---
