# MiMo Harness

A production-grade AI agent harness powered by Xiaomi MiMo model, following Claude Code architecture patterns. Provides coding assistance, file management, web search, document creation, task management, notebook editing, and more.

> Part of the [Agent Learning Hub](https://github.com/datawhalechina/Agent-Learning-Hub) project.

## Features

- **Agent Loop**: Dependency injection, circuit breaker, token budget tracking, 7 termination reasons, parallel tool dispatch, streaming responses, effort levels (low/medium/high)
- **Tool System**: 22 tools with concurrency-safe/unsafe markers, input validation, disk spillover for large outputs, background execution
- **Permission Pipeline**: 6 modes (default/plan/auto/accept_edits/dont_ask/bypass), 4-stage pipeline (validate → rules → context → prompt), path-scoped rules, protected paths (.git, .env, etc.)
- **Context Management**: LLM-based semantic compression with thrashing protection, progressive truncation (snip → microcompact → orphan filter), instruction preservation after compression
- **Memory System**: 4 typed memories (user/feedback/project/reference), MEMORY.md index, @import syntax, path-scoped rules (`.mimo/rules/*.md`)
- **Session Management**: Auto-save (JSONL), session resume (`--continue`/`--resume`), named sessions, multi-file checkpoint batch with /rewind
- **Settings Hierarchy**: 4-level config (managed → user → project → local), deny rules accumulate and cannot be overridden
- **Hook System**: 18 lifecycle events (PreToolUse, PostToolUse, Stop, PreCompact, TaskCreated, etc.), command/function hooks, matcher patterns
- **CLI**: Interactive REPL with pipe input, output formats (text/json/stream-json), bare mode, `!command` prefix, `/context` token breakdown

## Quick Start

```bash
# 1. Install
cd mimo-harness
pip install -e .

# 2. Configure API
cp .env.example .env
# Edit .env with your MiMo API key

# 3. Run
mimo-harness --task "What is 247 * 893?"
mimo-harness  # Interactive mode
```

## Usage

### Single Task
```bash
mimo-harness --task "Create a Python script that generates fibonacci numbers"
mimo-harness --task "Search the web for latest AI news"
mimo-harness --task "Read the README.md and summarize it"
```

### Pipe Input
```bash
cat error.log | mimo-harness -p "Analyze these errors and suggest fixes"
cat data.csv | mimo-harness -p "Summarize the key statistics"
```

### Interactive Mode
```bash
mimo-harness
# Prompt shows real-time token usage:
# You [5.4K/200.0K]: ████---------------------------------------- 2.7%

# or with options:
mimo-harness --auto-approve   # Skip confirmation prompts
mimo-harness --dry-run        # Show actions without executing
mimo-harness --plan           # Read-only mode (no writes)
mimo-harness --verbose        # Show trace logs
mimo-harness -c config.json   # Load configuration file
mimo-harness --bare           # Skip memory loading for speed
mimo-harness --effort high    # High effort (more tokens, higher temp)
mimo-harness --output-format json  # JSON output for scripting
```

### Session Resume
```bash
mimo-harness --continue       # Resume most recent session
mimo-harness --resume         # Pick a session to resume
mimo-harness --name "refactor-auth" --session-dir ~/.mimo/sessions/
```

### Commands (Interactive Mode)
| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/quit` | Exit |
| `/clear` | Clear conversation |
| `/tools` | List available tools with markers |
| `/save <path>` | Save session |
| `/load <path>` | Load session |
| `/dry-run` | Toggle dry-run mode |
| `/auto` | Toggle auto-approve mode |
| `/plan` | Toggle plan mode (read-only) |
| `/memory` | List stored memories |
| `/remember` | Save context as memory |
| `/hooks` | List registered hooks |
| `/stats` | Show session statistics |
| `/tokens` | Show current token usage with progress bar |
| `/compact` | Manually compress conversation context |
| `/context` | Show per-message token breakdown |
| `/init` | Scan project and generate AGENTS.md |
| `/rewind` | Restore files from the last checkpoint |
| `!<cmd>` | Run shell command directly (e.g. `!ls -la`) |

## Architecture

```
mimo_harness/
├── agent.py          # Core loop: DI, circuit breaker, token budget, effort levels
├── cli.py            # Interactive REPL, pipe input, output formats, session resume
├── config.py         # Environment configuration (lazy API key)
├── context.py        # Progressive compression, session management, checkpoints, @import
├── hooks.py          # 18 lifecycle events, command/function hooks
├── logging_utils.py  # Structured logging with trace IDs
├── memory.py         # Typed memory system (user/feedback/project/reference)
├── permissions.py    # 6 modes, 4-stage pipeline, protected paths
├── settings.py       # 4-level settings hierarchy (managed/user/project/local)
├── project_scanner.py # /init: detect language/framework/tools, generate AGENTS.md
├── security_pipeline.py # 2-layer security: regex + model classifier
└── tools/
    ├── registry.py   # Tool registration, validation, dispatch, disk spillover
    ├── file_ops.py   # File read/write/edit/glob/grep with output modes
    ├── shell.py      # Shell execution with compound parsing, credential scrubbing
    ├── code_exec.py  # Python code execution
    ├── web_tools.py  # Web search & fetch (SSRF protection, response cache)
    ├── doc_tools.py  # Document creation
    ├── math_tools.py # Safe math evaluation (AST-based)
    ├── interactive.py # AskUserQuestion multi-choice tool
    ├── monitor.py    # Background process monitoring
    ├── notebook_tools.py # Jupyter notebook cell editing
    ├── task_tools.py # Task management (create/get/list/update/delete)
    ├── plan_tools.py # Plan mode workflow
    ├── lsp_tools.py  # LSP integration (definition/references/diagnostics)
    └── scheduler_tools.py # Session-scoped cron scheduling
```

### Agent Loop (Ch2: Dialog Loop)
```
User Task → System Prompt + Context → LLM (MiMo)
    ↓
Tool Call? → Permission Pipeline → Execute → Feed Result Back → Loop
    ↓                                    ↓
No Tool Call → Final Response      Circuit Breaker / Token Budget
```

### Permission Pipeline (Ch4: 4-Stage, 6 Modes)
```
Modes: default | plan | auto | accept_edits | dont_ask | bypass

Stage 1: validateInput (parameter validation)
    ↓
Stage 2: Rule matching (deny > ask > allow)
    ↓
Stage 3: Context evaluation (plan mode, protected paths, tool-specific)
    ↓
Stage 4: Interactive prompt (user confirmation)

Protected paths: .git, .env, .bashrc, .zshrc, .vscode, .idea, .claude, .mimo
Bypass mode circuit breaker: blocks rm -rf /, mkfs, dd, fork bombs, shutdown
```

### Context Compression (Ch7: Token-Based, Claude Code Style)
```
Context Window: 200K tokens (Claude Code standard)
├── Startup reserve:  10K (system prompt + memory + AGENTS.md)
└── Compression trigger: 170K tokens (85% of window)

Compression produces a single summary (~1-10K tokens):
  1. LLM Summarize  — Structured summary of entire conversation (preferred)
  2. Truncation      — System marker + last 2 messages (fallback)

After compression: ~190K tokens available for continued work.

Thrashing protection: after 3 consecutive compression failures (<30% reduction),
auto-compaction is skipped and a warning is emitted.
Project instructions are preserved across compression via _extract_instructions().
```

### Memory System (Ch6: Four Types)
| Type | Purpose | Example |
|------|---------|---------|
| user | User profile, preferences | "Prefers TypeScript over JavaScript" |
| feedback | Validated practices, corrections | "Always run lint before commit" |
| project | Decisions, deadlines | "Using event-driven architecture" |
| reference | External links, dashboards | "Monitoring at Grafana X" |

## Configuration

### Settings Hierarchy (4 levels)
Later levels override earlier ones; deny rules accumulate across all levels.
```
managed:  .mimo/managed.json          (enterprise, cannot be overridden)
user:     ~/.mimo/settings.json       (user-level)
project:  .mimo/settings.json         (project-level, committable)
local:    .mimo/settings.local.json   (project-level, gitignored)
```

### Environment (.env)
```
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_API_KEY=your-api-key-here
MIMO_MODEL=mimo-v2.5-pro
```

### Permission Rules (.mimo/permissions.json)
```json
{
  "permissions": {
    "allow": ["read_file", "glob_files", "grep_files", "run_command:git:*"],
    "deny": ["run_command:rm -rf *"],
    "ask": ["write_file", "edit_file"]
  }
}
```

### Hooks (.mimo/config.json)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {"type": "command", "command": "echo ok", "timeout": 5}
        ]
      }
    ]
  }
}
```

## Tool Markers

Each tool has safety markers (Ch3: fail-closed defaults):
- **RO** (Read-Only): Auto-approved, no side effects
- **CS** (Concurrency-Safe): Can run in parallel with other CS tools
- **DST** (Destructive): Requires explicit confirmation

| Tool | Permission | RO | CS | Description |
|------|-----------|----|----|-------------|
| read_file | READ | ✓ | ✓ | Read file contents with line range |
| write_file | WRITE | | | Write content to file |
| edit_file | WRITE | | | Replace text in file |
| glob_files | READ | ✓ | ✓ | Find files by pattern (.gitignore support) |
| grep_files | READ | ✓ | ✓ | Search file contents (3 output modes) |
| run_command | DYNAMIC | | | Execute shell commands (compound parsing, credential scrubbing) |
| execute_python | WRITE | | | Run Python code |
| web_search | READ | ✓ | ✓ | DuckDuckGo search |
| web_fetch | READ | ✓ | ✓ | Fetch URL content (SSRF protection, 15min cache) |
| create_doc | WRITE | | | Create markdown/txt |
| create_spreadsheet | WRITE | | | Create CSV |
| calculator | READ | ✓ | | Safe math evaluation |
| ask_user_question | READ | ✓ | | Multi-choice interactive questions |
| monitor_start | WRITE | | | Start background process monitor |
| monitor_stop | WRITE | | | Stop a running monitor |
| monitor_list | READ | ✓ | | List active monitors |
| notebook_edit | WRITE | | | Edit Jupyter notebook cells (replace/insert/delete) |
| task_create | READ | ✓ | | Create a task |
| task_get | READ | ✓ | ✓ | Get task details |
| task_list | READ | ✓ | ✓ | List all tasks |
| task_update | READ | ✓ | | Update a task |
| task_delete | READ | ✓ | | Delete a task |

## Testing

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

923 tests across 19 test files:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_agent.py | 47 | DI, circuit breaker, token budget, retry, compression, parallel dispatch, streaming, CLAUDE.md survival, tool calls, AttrBag, effort levels |
| test_cli.py | 88 | REPL commands, main function paths, config integration, arg parsing, token formatting, pipe input, output formats, bare mode, !command, /context, session resume |
| test_config.py | 4 | Env vars, defaults, API key validation |
| test_permissions.py | 49 | 6 modes, 4-stage pipeline, rule matching, plan mode, protected paths, path-scoped rules, BYPASS circuit breaker |
| test_context.py | 96 | Token-based compression, LLM compression, thrashing protection, instruction preservation, @import, path-scoped rules, session from_jsonl, checkpoint batch |
| test_registry.py | 27 | Validation, dispatch, disk spillover, result budget |
| test_hooks.py | 25 | 18 lifecycle events, command/function hooks, subprocess execution, async hooks, hook chaining |
| test_logging.py | 11 | TraceLogger init, trace/info/error, tool_call, session_summary, file handler, verbose mode |
| test_memory.py | 14 | Typed storage, frontmatter, validation |
| test_tools.py | 100 | File ops, shell, code exec, math, web (mocked HTTP), interactive, monitor, doc tools, background jobs, streaming, compound command parsing, credential scrubbing |
| test_stress_boundary.py | 75 | Path traversal, SSRF, shell injection, large input, Unicode, permissions, concurrency, background jobs, monitors |
| test_project_scanner.py | 20 | Language/framework detection, AGENTS.md generation |
| test_settings.py | 20 | 4-level hierarchy, deny rule accumulation, get/get_nested, malformed files |
| test_notebook_tools.py | 18 | Replace/insert/delete modes, cell ID/index lookup, error cases |
| test_task_tools.py | 36 | CRUD operations, thread safety, status transitions, deleted task filtering |
| test_security_pipeline.py | 47 | Regex classifier, model classifier, output sanitization, prompt injection detection |
| test_lsp_tools.py | 39 | LSP client, definition/references/diagnostics, grep-based fallback |
| test_plan_tools.py | 19 | Enter/exit plan mode workflow |
| test_scheduler_tools.py | 51 | Cron parsing, job CRUD, scheduler firing, thread safety |

## Performance

Benchmark results:
- Tool registry: 142K executions/sec
- Permission checks: 67K checks/sec (100 rules)
- Context compaction: 800 messages → 30 in <1ms
- Concurrent tools: 20 parallel in 3ms
- Memory: 30 saves in 151ms, index auto-rebuild
- Full test suite: 923 tests in ~65 seconds

## License

MIT License. See [LICENSE](../LICENSE) for details.
