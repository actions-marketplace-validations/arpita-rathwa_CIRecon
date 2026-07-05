# CIRecon

> Agentic CI/CD repair for GitHub Actions — detects broken workflow files, auto-fixes what it can, and opens a PR with the rest.

[![CI](https://github.com/arpita-rathwa/CIRecon/actions/workflows/ci.yml/badge.svg)](https://github.com/arpita-rathwa/CIRecon/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Marketplace-orange)](https://github.com/marketplace/actions/cirecon)

---

## The problem

A misindented YAML block, a deprecated action version, a `needs:` reference pointing to a renamed job — any of these silently breaks your entire pipeline. You push, CI fails, you read the logs, you edit the YAML, you push again. CIRecon eliminates this loop.

---

## What it does

CIRecon runs automatically when you push changes to `.github/workflows/`. It:

1. Scans every workflow file with a deterministic rule engine (7 rules in v2)
2. Auto-fixes everything it can confidently repair
3. Uses an agentic Claude-powered loop for issues that need reasoning
4. Validates every fix before committing — no broken patches ever land
5. Generates a structured **Job Summary** in the GitHub Actions UI
6. Opens a pull request with a full audit trail of what was fixed and what needs attention

You review, you merge. CIRecon never touches your main branch directly.

---

## Quickstart

Add this to any workflow file in your repo:

```yaml
name: CIRecon

on:
  push:
    paths:
      - '.github/workflows/**'

jobs:
  cirecon:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: arpita-rathwa/CIRecon@v2
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

> `anthropic-api-key` is optional. Without it, CIRecon runs in rule-engine-only mode — still fixes the majority of common issues for free.

---

## What CIRecon checks

| Rule | Description | Severity | Auto-fixable |
|---|---|---|---|
| `RULE_DEPRECATED_ACTION` | Detects actions pinned to outdated versions (e.g. `checkout@v2` → `@v4`). Skips SHA-pinned actions. | Medium | ✅ Yes |
| `RULE_MISSING_PERMISSIONS_BLOCK` | Flags workflows with no top-level `permissions:` block. Without it, `GITHUB_TOKEN` has broad default access. | Medium | ✅ Yes |
| `RULE_BROKEN_NEEDS_DEPENDENCY` | Catches jobs with `needs:` referencing non-existent job IDs. | Medium | ❌ — flagged for review |
| `RULE_SECRET_IN_RUN_COMMAND` | Detects `${{ secrets.* }}` embedded in `run:` shell commands (leaks in logs). | Critical | ❌ — flagged for review |
| `RULE_PULL_REQUEST_TARGET_UNSAFE` | Flags `pull_request_target` + `actions/checkout` with the attacker-controlled PR ref. | Critical | ❌ — flagged for review |
| `RULE_OVERLY_BROAD_PERMISSIONS` | Detects `write-all` or ≥3 write-level permissions at top-level or job-level. | High | ❌ — flagged for review |
| `RULE_UNPINNED_THIRD_PARTY_ACTION` | Flags third-party actions not pinned to a full 40-char commit SHA. | High | ❌ — flagged for review |

More rules welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) to add your own.

---

## How it works

```
push event
    → rule engine scans all .github/workflows/*.yml
    → deterministic fixes applied + validated
    → agent loop (Claude) handles remaining issues
    → pull request opened with full audit trail
```

CIRecon is designed **deterministic-first** — the rule engine runs before any LLM call. Claude is only invoked for issues that static analysis can't resolve with confidence. This keeps costs low and behaviour predictable.

At the end of every run, CIRecon writes a **Job Summary** (`$GITHUB_STEP_SUMMARY`) with a table of all issues found, fixed, and unresolved — visible directly in the GitHub Actions UI.

Per-repo memory at `.github/cirecon/memory.json` means CIRecon learns from past runs — it won't re-suggest fixes that were previously rejected, and it recognises recurring patterns over time.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design.

---

## Configuration

### Scan mode (default)

| Input | Description | Default |
|---|---|---|
| `anthropic-api-key` | Anthropic API key — enables Claude-powered fallback for issues the rule engine can't fix | _(optional)_ |
| `github-token` | GitHub token with `contents: write` and `pull-requests: write` | _(required)_ |
| `max-iterations` | Maximum agent loop iterations per run | `10` |
| `fail-on-unresolved` | Exit with error if issues remain unresolved | `false` |
| `claude-model` | Claude model for LLM fallback (e.g. `claude-sonnet-4-20250514`) | `claude-haiku-4-5-20251001` |

### Dashboard mode

Set `mode: dashboard` and provide a comma-separated list of repos to scan:

| Input | Description | Default |
|---|---|---|
| `mode` | Set to `dashboard` to scan multiple repos | `scan` |
| `repos` | Comma-separated list of `owner/repo` to scan | _(required in dashboard mode)_ |
| `gist-id` | Existing Gist ID to update (omit to create a new Gist) | _(optional)_ |

Dashboard mode clones each repo (shallow, depth=1), runs all 7 rules, computes a health score per repo, and publishes a markdown dashboard to a **GitHub Gist** (also appended to the Job Summary).

---

## Example PR

When CIRecon finds and fixes issues, it opens a PR like this:

```
[CIRecon] Auto-fix 3 CI/CD workflow issue(s)

Files scanned: 2
Issues found: 3
Issues auto-fixed: 2
Requires human attention: 1

Fixed Issues
─────────────────────────────────────────────────
deploy.yml  | RULE_DEPRECATED_ACTION       | actions/checkout@v2 → @v4   | ✅
test.yml    | RULE_MISSING_PERMISSIONS_BLOCK| Added permissions block      | ✅

Unresolved Issues
─────────────────────────────────────────────────
release.yml | RULE_BROKEN_NEEDS_DEPENDENCY | Job 'deploy' needs 'build'
              which does not exist — please fix manually
```

---

## Why not just use actionlint?

`actionlint` is a great static linter — CIRecon respects it. The difference:

| | actionlint | CIRecon |
|---|---|---|---|
| Detects issues | ✅ | ✅ |
| Auto-fixes issues | ❌ | ✅ |
| Opens a PR with fixes | ❌ | ✅ |
| LLM fallback for complex issues | ❌ | ✅ |
| Per-repo memory | ❌ | ✅ |
| Job Summary in Actions UI | ❌ | ✅ |
| Org-wide dashboard (Gist) | ❌ | ✅ |
| Free to use | ✅ | ✅ |

---

## Contributing

CIRecon is designed to be extended. Adding a new rule takes about 15 minutes — see [CONTRIBUTING.md](CONTRIBUTING.md) for a step-by-step guide.

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built by [@arpita-rathwa](https://github.com/arpita-rathwa)*
