# AGENTS.md

## Project Overview

speckit-skills transforms GitHub's [spec-kit](https://github.com/github/spec-kit) SDD workflow into the portable [Agent Skills](https://agentskills.io) format (9 skills).
The only application code is `mise-tasks/generate.py`. The `skills/` directory is **generated output** -- never edit files there by hand.

## Tech Stack

- **Language**: Python 3.14+
- **Package manager**: [uv](https://docs.astral.sh/uv/) (managed via mise)
- **Task runner**: [mise](https://mise.jdx.dev/) (inline tasks in `mise.toml`, file tasks in `mise-tasks/`)
- **Dependencies**: `pyyaml`, `specify-cli` (from spec-kit)
- **Dev tools**: `ruff` (linter/formatter), `basedpyright` (type checker)

## Build / Lint / Test Commands

### Setup

```sh
mise install        # Install uv and Python toolchain
uv sync             # Install Python deps (mise does this automatically via prepare)
```

### Build

```sh
mise run generate   # Run specify init, copy/patch skills, verify output
```

### Linting & Type Checking

```sh
mise run lint           # ruff check
mise run lint:fix       # ruff check --fix
mise run format         # ruff format
mise run format:check   # ruff format --check
mise run typecheck      # basedpyright
mise run check          # lint + format:check + typecheck
mise run check:fix      # lint:fix + format + typecheck
```

## Architecture Notes

### Patch System

`generate.py` uses a declarative patch system with `(old, new)` replacement pairs:

- `SKILL_PATCHES`: skill-specific, keyed by skill name and relative file path.
- `COMMON_PATCHES`: applied to all files after skill-specific patches.
- `FORBIDDEN_PATTERNS`: regex patterns verified absent from all output.

### Adding a New Skill

1. Add the skill name and resources to `SKILLS` dict in `generate.py`.
2. Add skill-specific patches to `SKILL_PATCHES`.
3. Run `mise run generate` and verify output.

### Updating specify-cli

When the CI `generate` job fails with `ERROR: forbidden patterns found in output` after a version bump, upstream templates have introduced new `.specify/` or `$ARGUMENTS` patterns not yet covered by patches.

1. Run `uv add "specify-cli @ git+https://github.com/github/spec-kit.git@vX.Y.Z"` to update `pyproject.toml` and `uv.lock`.
2. Run `mise run generate` locally — check `skills/` for remaining violations, trace originals in `.agents/skills/`.
3. Add/update `COMMON_PATCHES` (shared) or `SKILL_PATCHES` (skill-specific) until `Step 3: Verifying output... OK`.
