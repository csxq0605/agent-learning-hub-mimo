# Gap Analysis: MiMo Harness vs Claude Code + Codex CLI

> Comprehensive comparison based on Claude Code official documentation (code.claude.com), OpenAI Codex CLI (developers.openai.com/codex), and deep audit of mimo-harness codebase.

## Executive Summary

MiMo Harness has a solid foundation (16 tools, 4-stage permissions, LLM-based compression, memory system, hooks), but significant gaps exist compared to Claude Code (40+ tools, MCP, sub-agents, streaming, worktrees, OS-level sandboxing, 30+ hook events) and Codex CLI (platform-native sandboxing, auto-review agent, image I/O, cloud tasks). This document categorizes gaps by priority and provides an optimization roadmap.

### Deep Audit Summary (2026-05-25 refresh)

After reviewing Claude Code official docs (code.claude.com/docs) and Codex CLI docs (developers.openai.com/codex), the following **critical security and correctness gaps** were identified beyond the original analysis:

| # | Gap | Severity | Claude Code Reference | Codex Reference |
|---|-----|----------|----------------------|-----------------|
| S1 | `write_file()` has no read-before-write check for existing files | **Critical** | Write tool requires read first | File write within sandbox roots |
| S2 | Shell compound commands not parsed for permission matching | **Critical** | `&&`, `||`, `;`, `|` each matched independently | Sandbox constrains entire execution |
| S3 | No credential scrubbing for subprocesses | **High** | `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | Sandbox env isolation |
| S4 | No protected paths (.git, config files) | **High** | `.git`, `.vscode`, `.claude` never auto-approved | `.git`, `.agents`, `.codex` always read-only |
| S5 | Large tool outputs truncated, not saved to disk | **Medium** | Bash >30K saved to file with preview | Output display in TUI |
| S6 | Hook system missing 20+ events | **Medium** | 30+ events including PreCompact, TaskCreated | N/A |
| S7 | Only 3 permission modes (vs Claude Code's 6) | **Medium** | default, acceptEdits, plan, auto, dontAsk, bypass | on-request, untrusted, never |
| S8 | No process wrapper stripping before permission matching | **Medium** | `timeout`, `nice`, `nohup` stripped | N/A |
| S9 | `_is_readonly()` blocks all chaining operators (too strict) | **Low** | Subcommands matched independently | Sandbox-based |
| S10 | No output_mode/files_with_matches/count for grep | **Low** | Three output modes via ripgrep | N/A |
| S11 | Glob ignores .gitignore by default | **Low** | Configurable via env var | N/A |
| S12 | No session checkpoints/rewind | **Medium** | Every edit snapshotted, Esc twice to rewind | N/A |
| S13 | Shell environment doesn't persist across commands | **Low** | Env vars don't persist (same) | N/A |
| S14 | WebFetch has no response cache | **Low** | 15-minute cache | N/A |
| S15 | No `--append-system-prompt` CLI flag | **Low** | Supported | N/A |
| S16 | No `--fallback-model` for overload | **Low** | Supported | N/A |
| S17 | No `dontAsk` permission mode | **Medium** | Auto-denies unapproved tools | `never` approval policy |
| S18 | Async hook doesn't pass stdin input | **Bug** | N/A | N/A |
| S19 | `_is_readonly()` missing common safe prefixes (grep, find, file, stat) | **Low** | Full Bash permission rules | N/A |
| S20 | No disk spillover for oversized tool results | **Medium** | `BASH_MAX_OUTPUT_LENGTH` with file save | TUI display |

---

## 1. TOOLS GAP

### 1.1 Tools Present in Claude Code but Missing from MiMo Harness

| Priority | Tool | Claude Code Description | MiMo Status |
|----------|------|------------------------|-------------|
| **P0** | `AskUserQuestion` | Multi-choice questions for requirements gathering | **MISSING** — no interactive clarification mechanism |
| **P0** | `EnterPlanMode`/`ExitPlanMode` | Switch to read-only planning mode mid-conversation | **PARTIAL** — `plan_mode` is constructor-only, can't toggle mid-conversation |
| **P0** | `Monitor` | Background process watching, streams output lines as events | **MISSING** |
| **P1** | `NotebookEdit` | Jupyter notebook cell editing (replace/insert/delete) | **MISSING** |
| **P1** | `LSP` | Language server integration (jump-to-def, find references, type errors) | **MISSING** |
| **P1** | `Glob` (enhanced) | `**` recursive, sorted by mtime, 100 cap, `.gitignore` respect | **PARTIAL** — `glob_files` exists but limited |
| **P1** | `Grep` (enhanced) | Context lines (-A/-B/-C), multiline, type filtering, ripgrep-based | **PARTIAL** — `grep_files` exists but no context lines |
| **P1** | `WebSearch` | Anthropic-backed web search with domain filtering | **PARTIAL** — uses DuckDuckGo HTML scraping |
| **P2** | `TaskCreate`/`TaskGet`/`TaskList`/`TaskUpdate` | Persistent task list with dependencies | **MISSING** |
| **P2** | `CronCreate`/`CronDelete`/`CronList` | Session-scoped scheduled tasks | **MISSING** |
| **P2** | `PushNotification` | Desktop/mobile push notifications | **MISSING** |
| **P2** | `PowerShell` | Native PowerShell execution on Windows | **MISSING** — uses Bash only |
| **P3** | `Skill` | Reusable prompt-based workflow execution | **MISSING** |
| **P3** | `SendMessage` | Agent team communication | **MISSING** |

### 1.2 Tools Present in Codex CLI but Missing from MiMo Harness

| Priority | Feature | Codex Description | MiMo Status |
|----------|---------|------------------|-------------|
| **P1** | Image input | Paste/upload images, `-i` flag | **MISSING** |
| **P1** | Web search (cached) | Pre-indexed results, reduced prompt injection | **PARTIAL** — DuckDuckGo scraping is fragile |
| **P2** | `/review` command | Code review against branch/commit/uncommitted | **MISSING** |
| **P2** | Cloud tasks | `codex cloud` for remote execution | **MISSING** (out of scope for local harness) |
| **P3** | Image generation | `gpt-image-2` integration | **MISSING** (model-dependent) |

### 1.3 Tool Quality Gaps

| Tool | Claude Code Feature | MiMo Gap |
|------|-------------------|----------|
| `Edit` | Read-before-edit check, uniqueness enforcement, `replace_all` flag | Simple string replacement, no read-before-edit, no uniqueness check |
| `Bash` | 2-min default timeout, 10-min max, 30K char output cap, `run_in_background`, env persistence | 30s default, 8K output cap, no background execution |
| `Read` | Images, PDFs, Jupyter notebooks, offset/limit pagination | Text only, basic offset/limit |
| `Write` | Read-before-write for existing files | No such check |
| `Grep` | ripgrep-based, multiline, `.gitignore` respect, type filtering | Basic regex, no multiline, no `.gitignore` |
| `Glob` | `.gitignore` respect (configurable), mtime sorting | No `.gitignore` respect |
| `WebFetch` | Markdown conversion, 15-min cache, redirect handling, SSRF protection | HTML-to-text, SSRF protection, no cache |

---

## 2. ARCHITECTURE GAP

### 2.1 Agent Loop

| Feature | Claude Code | Codex CLI | MiMo Harness |
|---------|------------|-----------|--------------|
| Parallel tool dispatch | Yes — concurrent tool calls processed simultaneously | Yes | **NO** — sequential `for tc in tool_calls` loop |
| Streaming responses | Yes — real-time token streaming | Yes | **NO** — waits for full completion |
| Sub-agent delegation | Yes — `Agent` tool spawns sub-agents with own context | Yes — subagents on explicit request | **NO** |
| Max turns control | `--max-turns` flag | Config-based | `max_steps` (20 default) |
| Cost tracking | `--max-budget-usd` | Token usage display | **NO** |
| Session resume | `claude --resume`, `claude -c` | `codex resume` | **PARTIAL** — `/load` from JSON |
| Background sessions | `--bg`, agent view | `codex cloud` | **NO** |
| Fork session | `--fork-session` | N/A | **NO** |

### 2.2 Permission System

| Feature | Claude Code | Codex CLI | MiMo Harness |
|---------|------------|-----------|--------------|
| Permission modes | default, acceptEdits, plan, auto, bypassPermissions | auto, read-only, full-access | DEFAULT, PLAN, AUTO |
| Path-scoped rules | `Read(~/secrets/**)`, `Edit(/src/**)` | Writable roots | **NO** — tool-level only |
| Command patterns | `Bash(npm run *)`, `Bash(git diff *)` | Per-command-prefix rules | **PARTIAL** — `run_command:npm:*` |
| Domain rules | `WebFetch(domain:example.com)` | N/A | **NO** |
| Disallowed tools | `--disallowedTools` | N/A | **NO** — only allow/deny/ask |
| Auto mode classifier | Built-in classifier rules | N/A | **NO** — simple auto-approve |
| Rejection circuit breaker | Yes | N/A | **YES** — 3 rejections → fall through |

### 2.3 Context Management

| Feature | Claude Code | Codex CLI | MiMo Harness |
|---------|------------|-----------|--------------|
| Context window | 200K tokens | Model-dependent | 200K tokens |
| Compression trigger | 85% of window | Summarization | 85% of window |
| LLM-based compression | Yes — structured summary | Yes | **YES** — `llm_compress()` |
| CLAUDE.md survival | Re-read from disk after compact | N/A | **NO** — compressed away |
| `/compact` command | Manual trigger | N/A | **YES** |
| Token display | Real-time in prompt | Token usage display | **YES** — `[X.XK/200.0K]` |
| Session persistence | Auto-save, resume | Local session storage | Manual `/save`/`/load` |

### 2.4 Memory System

| Feature | Claude Code | Codex CLI | MiMo Harness |
|---------|------------|-----------|--------------|
| CLAUDE.md hierarchy | Managed → User → Project → Local | AGENTS.md | **PARTIAL** — flat loading |
| Auto memory | 4 types, auto-saved by Claude | N/A | **YES** — 4 types |
| Path-scoped rules | `.claude/rules/*.md` with `paths` frontmatter | Rules with per-command-prefix | **NO** |
| `@import` syntax | Import files into CLAUDE.md | N/A | **NO** |
| Memory toggle | `/memory` to enable/disable | N/A | **NO** |
| Memory validation | Stale date detection, missing refs | N/A | **YES** |

### 2.5 Hooks System

| Feature | Claude Code | Codex CLI | MiMo Harness |
|---------|------------|-----------|--------------|
| Lifecycle events | PreToolUse, PostToolUse, Stop, SessionStart, SessionEnd, etc. | N/A | PreToolUse, PostToolUse, Stop + 4 more |
| Matcher patterns | `Bash(npm *)`, `Edit(src/**)` | N/A | **PARTIAL** — exact/wildcard only |
| `if` conditions | Filter by tool name + arguments | N/A | **NO** |
| Priority ordering | userSettings > projectSettings > localSettings | N/A | **DOCUMENTED but not implemented** |
| Async hooks | Yes | N/A | **YES** — `async_mode` flag |
| Setup hooks | `--init`, `--maintenance` matchers | N/A | **NO** |

---

## 3. CLI GAP

| Feature | Claude Code | Codex CLI | MiMo Harness |
|---------|------------|-----------|--------------|
| Pipe input | `cat file \| claude -p "query"` | stdin support | **NO** |
| Session resume | `claude -c`, `claude -r "name"` | `codex resume --last` | **NO** |
| Named sessions | `--name`, `/rename` | N/A | **NO** |
| Output formats | text, json, stream-json | stdout | text only |
| `--bare` mode | Skip auto-discovery for speed | N/A | **NO** |
| `--append-system-prompt` | Append to default prompt | N/A | **NO** |
| `--fallback-model` | Auto-fallback on overload | N/A | **NO** |
| `--effort` level | low/medium/high/xhigh/max | N/A | **NO** |
| Shell completions | bash/zsh/fish | bash/zsh/fish | **NO** |
| `@file` fuzzy search | N/A | `@` triggers file search | **NO** |
| `!command` prefix | N/A | Run shell inline | **NO** |
| Theme support | N/A | `/theme` | **NO** |
| Prompt history | N/A | Ctrl+R search | **NO** |

---

## 4. TESTING GAP

| Area | Current Coverage | Gap |
|------|-----------------|-----|
| CLI (`cli.py`) | **0 tests** | No REPL command tests, no arg parsing tests, no config loading |
| Logging (`logging_utils.py`) | **0 tests** | TraceLogger completely untested |
| Hook command execution | Function hooks only | `_run_command_hook()` with subprocess not tested |
| Agent `run()` integration | Mocked LLM only | No test exercising real tool dispatch |
| Dynamic shell permission | Not tested | `_check_shell_permission()` untested |
| Session persistence | Basic save/load | No corrupt JSON test, no missing fields test |
| Config file loading | Not tested | `_load_config()` untested |
| System prompt caching | Not tested | Cache behavior untested |
| Web tools | URL validation only | Actual `web_search()`/`web_fetch()` not tested |
| Doc tools | Basic only | `create_spreadsheet` with dict/list rows not tested |

---

## 5. OPTIMIZATION PLAN

### Phase 1: Critical Tools & Architecture (P0)

1. **Parallel tool dispatch** — Use `is_concurrency_safe` markers, `concurrent.futures.ThreadPoolExecutor`
2. **Streaming responses** — Use `stream=True` in OpenAI API, yield tokens as they arrive
3. **`AskUserQuestion` tool** — Multi-choice interactive clarification
4. **`Monitor` tool** — Background process watching with event streaming
5. **Enhanced `Edit` tool** — Read-before-edit check, uniqueness enforcement, `replace_all`
6. **`EnterPlanMode`/`ExitPlanMode`** — Mid-conversation plan mode switching

### Phase 2: Tool Enhancements (P1)

7. **Enhanced `Grep`** — Context lines (-A/-B/-C), multiline, type filtering
8. **Enhanced `Glob`** — `.gitignore` respect, mtime sorting
9. **Enhanced `Bash`** — `run_in_background`, 10-min timeout, 30K output cap
10. **Enhanced `Read`** — Image support, PDF support
11. **`NotebookEdit` tool** — Jupyter notebook cell editing
12. **`LSP` tool** — Language server integration
13. **Path-scoped permission rules** — `Read(~/secrets/**)`, `Edit(/src/**)`
14. **Domain-scoped rules** — `WebFetch(domain:example.com)`

### Phase 3: CLI & UX (P2)

15. **Pipe input** — `cat file | mimo-harness -p "query"`
16. **Session resume** — `mimo-harness --resume`, `mimo-harness -c`
17. **Named sessions** — `--name` flag
18. **Output formats** — text, json, stream-json
19. **Shell completions** — bash/zsh/fish/PowerShell
20. **`--append-system-prompt`** — Append to default prompt
21. **`--fallback-model`** — Auto-fallback on overload
22. **Task management** — TaskCreate/TaskGet/TaskList/TaskUpdate

### Phase 4: Advanced Features (P2-P3)

23. **Sub-agent delegation** — `Agent` tool for spawning sub-agents
24. **MCP support** — Model Context Protocol server integration
25. **Skill system** — Reusable prompt-based workflows
26. **Path-scoped memory rules** — `.mimo/rules/*.md` with path frontmatter
27. **CLAUDE.md survival after compact** — Re-read from disk
28. **Hook `if` conditions** — Filter by tool name + arguments
29. **Hook priority ordering** — Implement documented priority system
30. **Cost tracking** — Token usage per session, budget limits

### Phase 5: Testing & Quality

31. **CLI tests** — REPL commands, arg parsing, config loading
32. **Logging tests** — TraceLogger methods
33. **Integration tests** — Agent run() with real tool dispatch
34. **Hook command tests** — Subprocess execution
35. **Session persistence tests** — Corrupt JSON, missing fields

---

## 6. IMPLEMENTATION PRIORITY MATRIX

```
Impact ↑
       │  [1] Parallel dispatch    [3] AskUser    [6] Monitor
  High │  [2] Streaming            [4] Edit+       [5] PlanMode
       │  [7] Grep+                [8] Glob+       [13] Path rules
       │  [9] Bash+                [10] Read+      [11] NotebookEdit
  Med  │  [14] Domain rules        [15] Pipe input [16] Session resume
       │  [17] Named sessions      [18] Output fmt [22] Task mgmt
       │  [23] Sub-agents          [24] MCP        [25] Skills
  Low  │  [26] Path-scoped memory  [27] Compact    [28] Hook conditions
       │  [29] Hook priority       [30] Cost track [31-35] Tests
       └──────────────────────────────────────────────────────────→
          Low                        Medium                    High
                              Effort →
```

---

## 7. QUICK WINS (Can implement now)

1. **Parallel tool dispatch** — ~50 lines in `agent.py`, uses existing `is_concurrency_safe` markers
2. **Streaming responses** — ~30 lines in `agent.py`, `stream=True` + token yield
3. **Enhanced Edit** — Add read-before-edit check, uniqueness check, `replace_all` flag
4. **Enhanced Bash** — Increase timeout to 10-min, output to 30K, add `run_in_background`
5. **Enhanced Grep** — Add `-A`/`-B`/`-C` context lines, multiline support
6. **Path-scoped permissions** — Extend `PermissionRule` with glob path matching
7. **CLAUDE.md survival** — Re-read from disk after compression in agent.py

---

## Files to Modify

| File | Changes |
|------|---------|
| `mimo_harness/agent.py` | Parallel dispatch, streaming, plan mode toggle, cost tracking |
| `mimo_harness/tools/file_ops.py` | Enhanced Edit (read-before-edit, uniqueness), enhanced Read (images), enhanced Glob/Grep |
| `mimo_harness/tools/shell.py` | `run_in_background`, increased timeouts/output |
| `mimo_harness/tools/registry.py` | Streaming support, parallel dispatch markers |
| `mimo_harness/permissions.py` | Path-scoped rules, domain rules, disallowed tools |
| `mimo_harness/context.py` | CLAUDE.md survival after compact |
| `mimo_harness/hooks.py` | `if` conditions, priority ordering |
| `mimo_harness/cli.py` | Pipe input, session resume, named sessions, output formats |
| `mimo_harness/memory.py` | Path-scoped rules, `@import` syntax |
| `tests/` | CLI tests, logging tests, integration tests, hook command tests |

---

## 8. DEEP AUDIT IMPLEMENTATION PLAN (S1-S20)

### Batch 1: Critical Security Fixes (S1, S2, S3, S4)

**S1: write_file read-before-write check**
- File: `mimo_harness/tools/file_ops.py`
- Add `_write_allowed_files` set tracking (like `_read_files`)
- `write_file()` checks if file exists → if yes, must be in `_read_files`
- Claude Code: "Write to an unread existing file fails with error"

**S2: Compound command parsing for permissions**
- File: `mimo_harness/tools/shell.py`
- Parse `&&`, `||`, `;`, `|`, `|&` to extract subcommands
- Match each subcommand independently against permission rules
- Claude Code: "Each subcommand matched independently"

**S3: Credential scrubbing**
- File: `mimo_harness/tools/shell.py`
- Add `_scrub_env()` that removes API keys, tokens, secrets from subprocess env
- Pattern: `MIMO_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `*_SECRET`, `*_TOKEN`
- Claude Code: `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`

**S4: Protected paths**
- File: `mimo_harness/permissions.py`
- Add `PROTECTED_PATHS` constant: `.git`, `.vscode`, `.idea`, `.claude`, `.env`, `.gitconfig`
- Add `PROTECTED_FILES`: `.gitconfig`, `.gitmodules`, `.bashrc`, `.zshrc`
- `check()` blocks writes to protected paths unless in bypass mode
- Claude Code: "never auto-approved except in bypassPermissions"

### Batch 2: Tool Hardening (S5, S8, S9, S10, S11, S14, S19, S20)

**S5+S20: Output disk spillover**
- File: `mimo_harness/tools/shell.py`, `mimo_harness/tools/registry.py`
- When output > 30K chars, save to `.mimo/outputs/<uuid>.txt`, return preview
- Configurable via `MIMO_MAX_OUTPUT_LENGTH` env var

**S8: Process wrapper stripping**
- File: `mimo_harness/tools/shell.py`
- Strip `timeout`, `time`, `nice`, `nohup`, `stdbuf` before matching
- Claude Code: "Process wrappers stripped before matching"

**S9: Relaxed chaining operator detection**
- File: `mimo_harness/tools/shell.py`
- Only block `;`, `|`, `&` when NOT part of `&&`, `||` (valid subcommand chains)
- Parse subcommands and match each independently (ties to S2)

**S10: Grep output modes**
- File: `mimo_harness/tools/file_ops.py`
- Add `output_mode` param: `files_with_matches` (default), `content`, `count`
- Add `head_limit`, `offset` for pagination
- Add `-n` (line numbers), `-i` (case insensitive), `-o` (only matching)

**S11: Glob .gitignore respect**
- File: `mimo_harness/tools/file_ops.py`
- Add optional `respect_gitignore` param (default True)
- Parse `.gitignore` patterns and filter matches

**S14: WebFetch response cache**
- File: `mimo_harness/tools/web_tools.py`
- Add `_fetch_cache` dict with TTL (15 min default)
- Cache key: URL hash

**S19: Extended readonly prefixes**
- File: `mimo_harness/tools/shell.py`
- Add: `grep`, `find`, `file`, `stat`, `env`, `printenv`, `set`, `alias`, `history`, `realpath`, `readlink`

### Batch 3: Permission Modes (S7, S17)

**S7: Additional permission modes**
- File: `mimo_harness/permissions.py`
- Add `ACCEPT_EDITS`: reads + file edits auto-approved, shell still asks
- Add `DONT_ASK`: only pre-approved tools, auto-deny rest
- Add `BYPASS`: everything allowed (circuit breaker only for `rm -rf /`)

**S17: dontAsk mode**
- Integrated into S7

### Batch 4: Hook System Enhancements (S6, S18)

**S6: Additional hook events**
- File: `mimo_harness/hooks.py`
- Add events: `PreCompact`, `PostCompact`, `TaskCreated`, `TaskCompleted`,
  `SubagentStart`, `SubagentStop`, `PermissionRequest`, `PermissionDenied`,
  `ConfigChange`, `CwdChanged`, `FileChanged`

**S18: Fix async hook stdin**
- File: `mimo_harness/hooks.py`
- `_run_async()` passes `hook_input` via stdin pipe to subprocess

### Batch 5: CLI Enhancements (S12, S15, S16)

**S12: Session checkpoints**
- File: `mimo_harness/context.py`, `mimo_harness/cli.py`
- Before each file edit, snapshot the file to `.mimo/checkpoints/<session>/<seq>/`
- `/rewind` command restores last checkpoint

**S15: --append-system-prompt**
- File: `mimo_harness/cli.py`
- Append custom text to system prompt

**S16: --fallback-model**
- File: `mimo_harness/cli.py`, `mimo_harness/agent.py`
- On 429/503, switch to fallback model

---

## 8. ROUND 2 IMPLEMENTATION SUMMARY (2026-05-25)

### New Files Created

| File | Feature | Description |
|------|---------|-------------|
| `mimo_harness/settings.py` | A1 | 4-level settings hierarchy (managed/user/project/local) with deny-rule precedence |
| `mimo_harness/tools/notebook_tools.py` | T3 | `notebook_edit` tool — replace/insert/delete modes on .ipynb cells |
| `mimo_harness/tools/task_tools.py` | T2 | 5 task tools (create/get/list/update/delete) with thread-safe TaskStore |

### Features Implemented

| ID | Feature | Files Modified | Status |
|----|---------|---------------|--------|
| A1 | Settings hierarchy | `settings.py` (new) | Done |
| A3+C2 | Session resume (`--continue`/`--resume`) | `cli.py` | Done |
| A4+X1 | Auto-save sessions (JSONL) | `context.py`, `cli.py` | Done |
| A5 | Path-scoped rules (`.mimo/rules/*.md`) | `context.py` | Done |
| A6 | @import syntax in CLAUDE.md | `context.py` | Done |
| A7 | Tool output disk spillover | `registry.py` | Done |
| A8 | Thrashing protection for compaction | `context.py`, `agent.py` | Done |
| A9 | Compact instruction preservation | `context.py` | Done |
| C1 | Pipe input (stdin) | `cli.py` | Done |
| C3 | Output formats (text/json/stream-json) | `cli.py` | Done |
| C4 | `--bare` mode | `cli.py`, `agent.py` | Done |
| C7 | `!command` prefix | `cli.py` | Done |
| C9 | `/context` command | `cli.py` | Done |
| C11 | Effort levels (low/medium/high) | `cli.py`, `agent.py` | Done |
| T2 | Task management tools | `task_tools.py` (new) | Done |
| T3 | NotebookEdit tool | `notebook_tools.py` (new) | Done |
| X2 | Multi-file checkpoint batch | `context.py`, `agent.py` | Done |

### Test Status
- **543 tests passing** (up from 441 in Round 1)
- All Round 1 tests updated for new `compact_context` tuple return signature
- Round 3 (test coverage for Round 2 features) in progress
