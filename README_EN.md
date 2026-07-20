# Web Novel Master

[中文](./README.md) | [English](./README_EN.md)

> A structured AI-assisted workflow for original Chinese web-fiction projects. It turns an idea into an outline, character records, chapter plans, naming ledgers, and continuity checks. It does not promise popularity or replace author judgment.

Web Novel Master works as a Claude Code or OpenClaw skill and includes local Python tools for project scaffolding and quality baselines.

## Start Here

```bash
git clone https://github.com/tinylion1024/web-novel-master.git
cd web-novel-master

python3 scripts/manage_novel_project.py init \
  --mode professional \
  --title "Harbor Echoes" \
  --genre "urban rebirth" \
  --golden-finger "memory through objects" \
  --core-tropes "breaking a deadlock" \
  --protagonist "Wenren Che" \
  --heroine "Ruan Qiyue" \
  --antagonist "Bai Yanchuan" \
  --chapters 3
```

The command creates a project in `web-novels/` with an outline, character records, chapter tasks, and a naming ledger. Run the baseline validator after writing:

```bash
python3 scripts/manage_novel_project.py validate ./web-novels/<project-directory>
```

See the [walkthrough](./docs/DEMO.md) and the [original starter example](./examples/urban-rebirth-starter/README.md) for expected outputs.

## What It Provides

- Four workflows: Fast, Professional, Industrial, and Instant.
- Character, place, organization, and artifact naming diversity checks.
- Chapter-level status, word-count, placeholder, and continuity baselines.
- Platform positioning, serial-writing, and source-verification templates.
- Original examples and structured references for Chinese web-fiction writing.

## Install As A Skill

### Claude Code

```bash
python3 scripts/install_skill.py --platform claude-code
```

### OpenClaw

```bash
openclaw skills install . --global
```

Read the full [installation and compatibility guide](./docs/INSTALLATION.md) before updating an existing installation.

## Use As A Template

This repository is a GitHub Template. Choose **Use this template** on GitHub to create a clean repository for your own novel project without inheriting this repository's commit history.

## Community And Contribution

- Questions, showcases, and feature ideas: [GitHub Discussions](https://github.com/tinylion1024/web-novel-master/discussions)
- Bugs and content requests: [Issue templates](https://github.com/tinylion1024/web-novel-master/issues/new/choose)
- Contribution rules and local checks: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Security reports: [SECURITY.md](./SECURITY.md)

## Boundaries

Use this project for original work. Do not submit unauthorized text, request imitation of a living author's distinctive expression, or treat market figures and platform rules as permanent facts. See [RESPONSIBLE_USE.md](./RESPONSIBLE_USE.md) for details.
