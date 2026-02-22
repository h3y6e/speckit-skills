# speckit-skills

GitHub's [spec-kit](https://github.com/github/spec-kit) Spec-Driven Development (SDD) workflow, packaged as portable [Agent Skills](https://agentskills.io).

## Install

```sh
npx skills add h3y6e/speckit-skills -s '*'
```

## Skills

| Skill                                                              | Description                                    |
| ------------------------------------------------------------------ | ---------------------------------------------- |
| [`speckit-constitution`](./skills/speckit-constitution/SKILL.md)   | Review and update the project constitution     |
| [`speckit-specify`](./skills/speckit-specify/SKILL.md)             | Create a new feature specification             |
| [`speckit-clarify`](./skills/speckit-clarify/SKILL.md)             | Clarify and prioritize open questions in specs |
| [`speckit-plan`](./skills/speckit-plan/SKILL.md)                   | Generate an implementation plan from a spec    |
| [`speckit-tasks`](./skills/speckit-tasks/SKILL.md)                 | Break a plan into actionable tasks             |
| [`speckit-analyze`](./skills/speckit-analyze/SKILL.md)             | Analyze specs for consistency and completeness |
| [`speckit-checklist`](./skills/speckit-checklist/SKILL.md)         | Generate a checklist for a task                |
| [`speckit-taskstoissues`](./skills/speckit-taskstoissues/SKILL.md) | Convert tasks to GitHub issues                 |
| [`speckit-implement`](./skills/speckit-implement/SKILL.md)         | Implement a task following the spec and plan   |

## Development

### Prerequisites

- [mise](https://mise.jdx.dev/)

### Setup

```sh
mise install
```

### Generate skills

```sh
mise run generate
```

### Lint & type check

```sh
mise run check          # lint + format check + type check
mise run check:fix      # lint fix + format + type check
```

See [AGENTS.md](AGENTS.md) for full development guidelines.

## License

[MIT](LICENSE)
