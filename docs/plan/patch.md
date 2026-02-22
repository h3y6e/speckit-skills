# skills/ Patch Plan

## Overview

The `skills/` output from `mise run generate` has hardcoded dependencies on the `.specify/` directory and `$ARGUMENTS` placeholders, preventing skills from working standalone. This document defines the patch processing in `generate.py`.

See [init.md](./init.md) for the overall generation pipeline.

## Patch System

`generate.py` uses a declarative patch system:

- **`COMMON_PATCHES`**: List of `(old, new)` pairs applied to all files
- **`SKILL_PATCHES`**: Skill name -> relative file path -> list of `(old, new)` pairs
- **`strip_metadata_frontmatter()`**: Removes `metadata:` block from SKILL.md YAML frontmatter
- **`FORBIDDEN_PATTERNS`**: Regex patterns for output verification: `.specify/` and `$ARGUMENTS`

Application order: skill-specific patches -> common patches (combined and applied in one pass per file).

## Common Patches (`COMMON_PATCHES`)

Applied to all files across all skills:

| #   | Target                            | Change                                         |
| --- | --------------------------------- | ---------------------------------------------- |
| C1  | `.specify/scripts/bash/` paths    | Replace with `scripts/`                        |
| C2  | `.specify/templates/` paths       | Replace with `references/`                     |
| C3  | `.specify/memory/constitution.md` | Replace with `specs/constitution.md`           |
| C4  | `compatibility:` line             | Delete entire line (replace with empty string) |
| C5  | `$ARGUMENTS` user input block     | Delete entire `## User Input` section          |
| C6  | `common.sh` fallback              | Change `../../..` relative path to `pwd`       |

### C4 Detail: `compatibility` Line Deletion

```yaml
# Before (entire line deleted)
compatibility: Requires spec-kit project structure with .specify/ directory
```

### C5 Detail: `$ARGUMENTS` User Input Block Deletion

```markdown
<!-- Before (entire block deleted) -->

## User Input

\`\`\`text
$ARGUMENTS
\`\`\`

You **MUST** consider the user input before proceeding (if not empty).
```

### C6 Detail: `common.sh` Repository Root Detection

```bash
# Before
    else
        # Fall back to script location for non-git repos
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi

# After
    else
        # Fall back to current directory for non-git repos
        pwd
    fi
```

## Skill-Specific Patches (`SKILL_PATCHES`)

### speckit-specify

**SKILL.md:**

- Rewrite `/speckit.specify` trigger description for Agent Skills context
- Replace `$ARGUMENTS` literal references with `"<feature-description>"` / `"<user description>"`
- Remove `"$ARGUMENTS"` argument from command examples

**references/spec-template.md:**

- `"$ARGUMENTS"` -> `"<user description>"`

**scripts/create-new-feature.sh:**

- Change `.git || .specify` marker search to `.git` only
- Template path: `$REPO_ROOT/.specify/templates/spec-template.md` -> `$SCRIPT_DIR/../references/spec-template.md`

### speckit-clarify

**SKILL.md:**

- Delete `$ARGUMENTS` context line

### speckit-constitution

**SKILL.md:**

- `.specify/templates/plan-template.md` -> `../speckit-plan/references/plan-template.md` (sibling skill reference)
- `.specify/templates/spec-template.md` -> `../speckit-specify/references/spec-template.md`
- `.specify/templates/tasks-template.md` -> `../speckit-tasks/references/tasks-template.md`
- `.specify/templates/commands/*.md` reference -> rewritten to reference SKILL.md in sibling speckit-\* directories

### speckit-plan

**scripts/setup-plan.sh:**

- Template path: `$REPO_ROOT/.specify/templates/plan-template.md` -> `$SCRIPT_DIR/../references/plan-template.md`

**scripts/update-agent-context.sh:**

- Template path: `$REPO_ROOT/.specify/templates/agent-file-template.md` -> `$SCRIPT_DIR/../references/agent-file-template.md`

### speckit-tasks

**SKILL.md:**

- Delete `$ARGUMENTS` context line

### speckit-checklist

**SKILL.md:**

- Replace `$ARGUMENTS` literal references with natural language expressions for user input

### speckit-analyze

**SKILL.md:**

- Delete `$ARGUMENTS` context section

## Template Copy Mapping

| Template                   | Destination Skill |
| -------------------------- | ----------------- |
| `spec-template.md`         | specify           |
| `plan-template.md`         | plan              |
| `tasks-template.md`        | tasks             |
| `checklist-template.md`    | checklist         |
| `constitution-template.md` | constitution      |
| `agent-file-template.md`   | plan              |

## Processing Flow

```
copy_and_patch_skills():

1. Delete and recreate skills/
2. For each skill:
   a. Copy .agents/skills/<name>/SKILL.md -> skills/<name>/SKILL.md
   b. Copy .specify/templates/ -> skills/<name>/references/ (per mapping)
   c. Copy .specify/scripts/bash/ -> skills/<name>/scripts/
   d. Strip metadata frontmatter from SKILL.md
   e. For all files: combine skill-specific + common patches and apply
```

## Output Verification

`verify_output()` scans all files under `skills/` for the following regex patterns:

- `\.specify/` -- references to `.specify/` directory
- `\$ARGUMENTS` -- unresolved placeholders

Any match causes `sys.exit(1)` failure.
