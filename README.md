# CIRecon

Agentic CI/CD workflow repair — detects and auto-fixes GitHub Actions errors.

![CI](https://github.com/arpita-rathwa/CIRecon/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## What it does

CIRecon scans your GitHub Actions workflow files, detects common issues like deprecated actions, missing permissions, or broken job dependencies, and automatically fixes them. It opens a pull request with all repairs applied so you can review before merging.

## Quickstart

```yaml
- uses: arpita-rathwa/CIRecon@v1
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## What CIRecon checks

| Rule | Description | Auto-fixable |
|---|---|---|
| Deprecated action versions | Detects outdated actions (e.g., `checkout@v2`) and suggests the latest version | Yes |
| Missing permissions block | Warns when no top-level `permissions` block is set | Yes |
| Broken `needs` dependencies | Flags jobs that depend on non-existent job IDs | No |

## How it works

CIRecon runs a static rule engine against every workflow file, applies deterministic fixes for auto-fixable issues, then optionally uses an agentic loop (powered by Claude) to resolve remaining issues. All validated patches are collected and opened as a single pull request. See [ARCHITECTURE.md](ARCHITECTURE.md) for full detail.

## Configuration

| Input | Description | Default |
|---|---|---|
| `anthropic-api-key` | Anthropic API key for LLM-based fix fallback | _(optional)_ |
| `max-iterations` | Maximum agent loop iterations | `10` |
| `fail-on-unresolved` | Exit with error if issues remain after repair | `false` |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add rules, run tests, and submit changes.

## License

MIT
