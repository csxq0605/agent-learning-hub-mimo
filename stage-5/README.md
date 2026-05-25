# Stage 5: Reusable Code Review Skill

## Deliverable
A reusable `code-review` skill with SKILL.md, review script, and smoke test.

## Skill vs Tool vs Prompt vs MCP

| Concept | What It Is | Example |
|---------|-----------|---------|
| **Tool** | A callable API endpoint | `read_file(path)` returns file contents |
| **Prompt** | A one-shot instruction | "Review this code for bugs" |
| **Skill** | A reusable workflow with steps, scripts, templates, and acceptance criteria | This code-review skill |
| **MCP** | A protocol to connect external tools/data sources | Jira MCP server for ticket access |

A Skill is **more than a prompt**: it has:
- Defined trigger conditions ("when to use")
- Step-by-step workflow
- Supporting scripts and templates
- Acceptance criteria for success
- A smoke test to verify it works

## Skill Structure

```
code-review-skill/
├── SKILL.md          # Skill definition (name, description, when to use, steps, acceptance criteria)
├── review.py         # Entry point script
└── templates/
    └── report.md     # Output template
```

## How to Run

```bash
pip install openai python-dotenv

# Smoke test (verifies the skill works)
python review.py --smoke-test

# Review a file
# 在 .env 中配置 MIMO_BASE_URL, MIMO_API_KEY, MIMO_MODEL
python review.py src/auth.py

# Review with specific focus
python review.py src/api.py --focus security
```

## References
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [OpenClaw Skills](https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md)
- [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401)
