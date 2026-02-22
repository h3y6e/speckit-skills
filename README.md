# speckit-skills

GitHub's [spec-kit](https://github.com/github/spec-kit) Spec-Driven Development (SDD) workflow, packaged as portable [Agent Skills](https://agentskills.io).

## Install

```sh
npx skills add h3y6e/speckit-skills
```

## Skills

| Skill                   | Description                                    |
| ----------------------- | ---------------------------------------------- |
| `speckit-constitution`  | Review and update the project constitution     |
| `speckit-specify`       | Create a new feature specification             |
| `speckit-clarify`       | Clarify and prioritize open questions in specs |
| `speckit-plan`          | Generate an implementation plan from a spec    |
| `speckit-tasks`         | Break a plan into actionable tasks             |
| `speckit-analyze`       | Analyze specs for consistency and completeness |
| `speckit-checklist`     | Generate a checklist for a task                |
| `speckit-taskstoissues` | Convert tasks to GitHub issues                 |
| `speckit-implement`     | Implement a task following the spec and plan   |

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
