#!/usr/bin/env python
# [MISE] description="Generate agent skills from spec-kit's output"
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
GENERATED_SKILLS_DIR = ROOT / ".agents" / "skills"
TEMPLATES_DIR = ROOT / ".specify" / "templates"
SCRIPTS_DIR = ROOT / ".specify" / "scripts" / "bash"
OUTPUT_DIR = ROOT / "skills"

# ---------------------------------------------------------------------------
# Skill definitions — single source of truth for what each skill contains
# ---------------------------------------------------------------------------

SKILLS: dict[str, dict[str, list[str]]] = {
    "speckit-specify": {
        "references": ["spec-template.md"],
        "scripts": ["common.sh", "create-new-feature.sh"],
    },
    "speckit-clarify": {
        "scripts": ["common.sh", "check-prerequisites.sh"],
    },
    "speckit-constitution": {
        "references": ["constitution-template.md"],
    },
    "speckit-plan": {
        "references": ["plan-template.md", "agent-file-template.md"],
        "scripts": ["common.sh", "setup-plan.sh", "update-agent-context.sh"],
    },
    "speckit-tasks": {
        "references": ["tasks-template.md"],
        "scripts": ["common.sh", "check-prerequisites.sh"],
    },
    "speckit-checklist": {
        "references": ["checklist-template.md"],
        "scripts": ["common.sh", "check-prerequisites.sh"],
    },
    "speckit-implement": {
        "scripts": ["common.sh", "check-prerequisites.sh"],
    },
    "speckit-analyze": {
        "scripts": ["common.sh", "check-prerequisites.sh"],
    },
    "speckit-taskstoissues": {
        "scripts": ["common.sh", "check-prerequisites.sh"],
    },
}

# ---------------------------------------------------------------------------
# Text patches
# ---------------------------------------------------------------------------

# Applied to all SKILL.md and references/ files.
COMMON_REPLACEMENTS: dict[str, str] = {
    ".specify/scripts/bash/": "scripts/",
    ".specify/templates/": "references/",
    ".specify/memory/constitution.md": "specs/constitution.md",
    "compatibility: Requires spec-kit project structure with .specify/ directory\n": "",
    "## User Input\n\n```text\n$ARGUMENTS\n```\n\nYou **MUST** consider the user input before proceeding (if not empty).\n\n": "",
}

# Skill-specific SKILL.md patches (applied after COMMON_REPLACEMENTS).
SKILL_MD_REPLACEMENTS: dict[str, dict[str, str]] = {
    "speckit-analyze": {
        "\n## Context\n\n$ARGUMENTS\n": "",
    },
    "speckit-clarify": {
        "\nContext for prioritization: $ARGUMENTS\n": "",
    },
    "speckit-tasks": {
        "\nContext for task generation: $ARGUMENTS\n": "",
    },
    "speckit-specify": {
        "The text the user typed after `/speckit.specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.": (
            "The user's message that triggered this skill **is** the feature description. Do not ask the user to repeat it unless they provided no description."
        ),
        '.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS"': ('.specify/scripts/bash/create-new-feature.sh --json "<feature-description>"'),
        '.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS" --json' + ' --number 5 --short-name "user-auth" "Add user authentication"': ('.specify/scripts/bash/create-new-feature.sh --json --number 5 --short-name "user-auth" "Add user authentication"'),
        '.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS" -Json' + ' -Number 5 -ShortName "user-auth" "Add user authentication"': ('.specify/scripts/bash/create-new-feature.sh --json -Number 5 -ShortName "user-auth" "Add user authentication"'),
    },
    "speckit-checklist": {
        "already unambiguous in `$ARGUMENTS`": "already unambiguous in the user's input",
        "Combine `$ARGUMENTS` + clarifying answers": ("Combine the user's input + clarifying answers"),
    },
}

# Reference file patches: relative path -> replacements.
REFERENCE_REPLACEMENTS: dict[str, dict[str, str]] = {
    "spec-template.md": {
        '"$ARGUMENTS"': '"<user description>"',
    },
}

# speckit-constitution references templates in sibling skills (applied before COMMON_REPLACEMENTS).
CONSTITUTION_REPLACEMENTS: dict[str, str] = {
    ".specify/templates/plan-template.md": "../speckit-plan/references/plan-template.md",
    ".specify/templates/spec-template.md": "../speckit-specify/references/spec-template.md",
    ".specify/templates/tasks-template.md": "../speckit-tasks/references/tasks-template.md",
    ("   - Read each command file in `.specify/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required."): (
        "   - Review all other speckit skill definitions (SKILL.md files in sibling speckit-* directories) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required."
    ),
}

# Script-specific patches: filename -> list of (old, new) pairs.
SCRIPT_DIR_EXPR = '$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)'

SCRIPT_REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "common.sh": [
        (
            '    else\n        # Fall back to script location for non-git repos\n        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n        (cd "$script_dir/../../.." && pwd)\n    fi',
            "    else\n        # Fall back to current directory for non-git repos\n        pwd\n    fi",
        ),
    ],
    "create-new-feature.sh": [
        (
            'if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then',
            'if [ -d "$dir/.git" ]; then',
        ),
        (
            'TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"',
            f'TEMPLATE="{SCRIPT_DIR_EXPR}/../references/spec-template.md"',
        ),
    ],
    "setup-plan.sh": [
        (
            'TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"',
            f'TEMPLATE="{SCRIPT_DIR_EXPR}/../references/plan-template.md"',
        ),
    ],
    "update-agent-context.sh": [
        (
            'TEMPLATE_FILE="$REPO_ROOT/.specify/templates/agent-file-template.md"',
            f'TEMPLATE_FILE="{SCRIPT_DIR_EXPR}/../references/agent-file-template.md"',
        ),
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def replace_all(text: str, replacements: dict[str, str]) -> str:
    """Apply multiple string replacements in order."""
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def patch_file(path: Path, replacements: dict[str, str] | list[tuple[str, str]]) -> bool:
    """Read a file, apply replacements, write back if changed. Returns True if patched."""
    original = path.read_text()
    if isinstance(replacements, dict):
        patched = replace_all(original, replacements)
    else:
        patched = original
        for old, new in replacements:
            patched = patched.replace(old, new)
    if patched != original:
        _ = path.write_text(patched)
        return True
    return False


def strip_metadata_frontmatter(path: Path) -> bool:
    """Remove the metadata block from YAML frontmatter. Returns True if changed."""
    original = path.read_text()
    # Match 'metadata:\n' followed by indented lines (sub-keys like author:, source:).
    patched = re.sub(r"metadata:\n(?:  .+\n)+", "", original)
    if patched != original:
        _ = path.write_text(patched)
        return True
    return False


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_specify_init() -> None:
    """Run specify init to generate base files."""
    print("Step 1: Running specify init...")
    result = subprocess.run(
        [
            "specify",
            "init",
            "--here",
            "--ai",
            "codex",
            "--ai-skills",
            "--force",
            "--ignore-agent-tools",
            "--script",
            "sh",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def copy_and_patch_skills() -> None:
    """Copy generated files into skills/ and apply all patches."""
    print("Step 2: Copying and patching skills...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    for skill_name, resources in SKILLS.items():
        src_skill_md = GENERATED_SKILLS_DIR / skill_name / "SKILL.md"
        if not src_skill_md.exists():
            print(f"  WARNING: {src_skill_md} not found, skipping.")
            continue

        out_dir = OUTPUT_DIR / skill_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Copy SKILL.md
        _ = shutil.copy2(src_skill_md, out_dir / "SKILL.md")
        print(f"  Copied  {skill_name}/SKILL.md")

        # Copy references/ (templates)
        for ref in resources.get("references", []):
            src = TEMPLATES_DIR / ref
            dst_dir = out_dir / "references"
            dst_dir.mkdir(exist_ok=True)
            if src.exists():
                _ = shutil.copy2(src, dst_dir / ref)
                print(f"  Copied  {skill_name}/references/{ref}")
            else:
                print(f"  WARNING: template {ref} not found.")

        # Copy scripts/
        for script in resources.get("scripts", []):
            src = SCRIPTS_DIR / script
            dst_dir = out_dir / "scripts"
            dst_dir.mkdir(exist_ok=True)
            if src.exists():
                _ = shutil.copy2(src, dst_dir / script)
                print(f"  Copied  {skill_name}/scripts/{script}")
            else:
                print(f"  WARNING: script {script} not found.")

        # Patch SKILL.md
        skill_md_path = out_dir / "SKILL.md"
        _ = strip_metadata_frontmatter(skill_md_path)
        if skill_name == "speckit-constitution":
            _ = patch_file(skill_md_path, CONSTITUTION_REPLACEMENTS)
        skill_md_extra = SKILL_MD_REPLACEMENTS.get(skill_name)
        if skill_md_extra:
            _ = patch_file(skill_md_path, skill_md_extra)
        if patch_file(skill_md_path, COMMON_REPLACEMENTS):
            print(f"  Patched {skill_name}/SKILL.md")

        # Patch references/
        refs_dir = out_dir / "references"
        if refs_dir.exists():
            for ref_file in refs_dir.iterdir():
                ref_extra = REFERENCE_REPLACEMENTS.get(ref_file.name)
                if ref_extra:
                    _ = patch_file(ref_file, ref_extra)
                if patch_file(ref_file, COMMON_REPLACEMENTS):
                    print(f"  Patched {skill_name}/references/{ref_file.name}")

        # Patch scripts
        scripts_dir = out_dir / "scripts"
        if scripts_dir.exists():
            for script_file in scripts_dir.iterdir():
                pairs = SCRIPT_REPLACEMENTS.get(script_file.name)
                if pairs and patch_file(script_file, pairs):
                    print(f"  Patched {skill_name}/scripts/{script_file.name}")


def print_summary() -> None:
    """Print summary of generated skills."""
    generated = sorted(d.name for d in OUTPUT_DIR.iterdir() if d.is_dir())
    print(f"Generated {len(generated)} skills in {OUTPUT_DIR.relative_to(ROOT)}/:")
    for name in generated:
        skill_dir = OUTPUT_DIR / name
        parts: list[str] = []
        refs = skill_dir / "references"
        scripts = skill_dir / "scripts"
        if refs.exists():
            parts.append(f"{len(list(refs.iterdir()))} refs")
        if scripts.exists():
            parts.append(f"{len(list(scripts.iterdir()))} scripts")
        extra = f" ({', '.join(parts)})" if parts else ""
        print(f"  {name}/{extra}")


# Patterns that must not remain in generated skills.
FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.specify/"),
    re.compile(r"\$ARGUMENTS"),
]


def verify_output() -> None:
    """Verify no forbidden patterns remain in generated skills. Exit on failure."""
    print("Step 3: Verifying output...")
    violations: list[str] = []
    for path in sorted(OUTPUT_DIR.rglob("*")):
        if not path.is_file():
            continue
        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(OUTPUT_DIR)
        for pattern in FORBIDDEN_PATTERNS:
            for match in pattern.finditer(content):
                violations.append(f"  {rel}: found '{match.group()}'")
    if violations:
        print("ERROR: forbidden patterns found in output:")
        for v in violations:
            print(v)
        sys.exit(1)
    print(f"  OK — {len(FORBIDDEN_PATTERNS)} patterns checked, 0 violations.")


def main() -> None:
    print("=== Generating Agent Skills from spec-kit ===\n")
    run_specify_init()
    print()
    copy_and_patch_skills()
    print()
    verify_output()
    print("\n=== Summary ===")
    print_summary()


if __name__ == "__main__":
    main()
