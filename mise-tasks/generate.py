#!/usr/bin/env python
# [MISE] description="Generate agent skills from spec-kit's output"
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

GENERATED_SKILLS_DIR = ROOT / ".agents" / "skills"
SPECIFY_DIR = ROOT / ".specify"
TEMPLATES_DIR = SPECIFY_DIR / "templates"
SCRIPTS_DIR = SPECIFY_DIR / "scripts" / "bash"
OUTPUT_DIR = ROOT / "skills"

SKILL_NAMES = [
    "speckit-specify",
    "speckit-clarify",
    "speckit-constitution",
    "speckit-plan",
    "speckit-tasks",
    "speckit-checklist",
    "speckit-implement",
    "speckit-analyze",
    "speckit-taskstoissues",
]

# Mapping: skill name -> list of template files to copy into references/
SKILL_REFERENCES: dict[str, list[str]] = {
    "speckit-specify": ["spec-template.md"],
    "speckit-clarify": ["spec-template.md"],
    "speckit-constitution": ["constitution-template.md"],
    "speckit-plan": ["plan-template.md", "agent-file-template.md"],
    "speckit-tasks": ["tasks-template.md"],
    "speckit-checklist": ["checklist-template.md"],
    "speckit-implement": [],
    "speckit-analyze": [],
    "speckit-taskstoissues": [],
}

# Mapping: skill name -> list of script files to copy into scripts/
SKILL_SCRIPTS: dict[str, list[str]] = {
    "speckit-specify": ["common.sh", "create-new-feature.sh"],
    "speckit-clarify": ["common.sh", "check-prerequisites.sh"],
    "speckit-constitution": [],
    "speckit-plan": ["common.sh", "setup-plan.sh", "update-agent-context.sh"],
    "speckit-tasks": ["common.sh", "check-prerequisites.sh"],
    "speckit-checklist": ["common.sh", "check-prerequisites.sh"],
    "speckit-implement": ["common.sh", "check-prerequisites.sh"],
    "speckit-analyze": ["common.sh", "check-prerequisites.sh"],
    "speckit-taskstoissues": ["common.sh", "check-prerequisites.sh"],
}


# ---------------------------------------------------------------------------
# Step 1: Run specify init
# ---------------------------------------------------------------------------


def run_specify_init() -> None:
    """Run specify init to generate base files."""
    print("Step 1: Running specify init...")
    cmd = [
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
    ]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print("  specify init completed.")


# ---------------------------------------------------------------------------
# Step 2: Copy files into skills/
# ---------------------------------------------------------------------------


def generate_skill(skill_name: str) -> None:
    """Copy generated files for a single skill into skills/."""
    print(f"  Processing {skill_name}...")

    src_skill = GENERATED_SKILLS_DIR / skill_name / "SKILL.md"
    if not src_skill.exists():
        print(f"    WARNING: {src_skill} not found, skipping.")
        return

    out_skill_dir = OUTPUT_DIR / skill_name
    out_skill_dir.mkdir(parents=True, exist_ok=True)

    # --- SKILL.md ---
    _ = shutil.copy2(src_skill, out_skill_dir / "SKILL.md")

    # --- references/ ---
    refs = SKILL_REFERENCES.get(skill_name, [])
    if refs:
        refs_dir = out_skill_dir / "references"
        refs_dir.mkdir(exist_ok=True)
        for ref_file in refs:
            src = TEMPLATES_DIR / ref_file
            if src.exists():
                _ = shutil.copy2(src, refs_dir / ref_file)
            else:
                print(f"    WARNING: template {ref_file} not found.")

    # --- scripts/ ---
    scripts = SKILL_SCRIPTS.get(skill_name, [])
    if scripts:
        scripts_dir = out_skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        for script_file in scripts:
            src = SCRIPTS_DIR / script_file
            if src.exists():
                _ = shutil.copy2(src, scripts_dir / script_file)
            else:
                print(f"    WARNING: script {script_file} not found.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=== Generating Agent Skills from spec-kit ===")
    print(f"Root: {ROOT}")
    print()

    # Step 1: Run specify init
    run_specify_init()
    print()

    # Step 2: Copy files into skills/
    print("Step 2: Copying files into skills/...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    for skill_name in SKILL_NAMES:
        generate_skill(skill_name)
    print()

    # Summary
    print("=== Done ===")
    generated = [d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()]
    print(f"Generated {len(generated)} skills in {OUTPUT_DIR.relative_to(ROOT)}/:")
    for name in sorted(generated):
        skill_dir = OUTPUT_DIR / name
        parts: list[str] = []
        if (skill_dir / "references").exists():
            parts.append(f"{len(list((skill_dir / 'references').iterdir()))} refs")
        if (skill_dir / "scripts").exists():
            parts.append(f"{len(list((skill_dir / 'scripts').iterdir()))} scripts")
        extra = f" ({', '.join(parts)})" if parts else ""
        print(f"  {name}/{extra}")


if __name__ == "__main__":
    main()
