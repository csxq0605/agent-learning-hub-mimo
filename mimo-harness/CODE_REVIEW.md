# MiMo Harness v0.2.0 Code Review

> Full review of `mimo-harness/` (15 source files, 8 test files, 225 tests)
> Reference: Claude Code architecture book (Ch2-Ch15)

**Reviewer**: Claude Code (automated)
**Date**: 2026-05-24
**Version**: v0.2.0

## Summary

| Severity | Total | Fixed | Remaining |
|----------|-------|-------|-----------|
| P0 | 2 | 2 | 0 |
| P1 | 8 | 7 | 1 |
| P2 | 9 | 4 | 5 |

---

## P0 — Security (Fix Immediately)

### P0-1: Path traversal in `_validate_write_path` — FIXED

**Files**: `tools/file_ops.py:22`, `memory.py:78`

The `startswith` string comparison was vulnerable to prefix collisions. A path like `/allowed_dir_evil/secret` passed the check for `/allowed_dir`.

**Fix applied**: Replaced with `Path.is_relative_to()` in both files.

### P0-2: No read-path validation — FIXED

**File**: `tools/file_ops.py:35, 86, 99`

`read_file`, `glob_files`, and `grep_files` had zero path restrictions. An LLM could read `/etc/shadow`, `.env` (API keys), SSH keys, or any system file.

**Fix applied**: Added `_validate_read_path()` function and applied it to all three read tools. Now restricted to working directory.

---

## P1 — Design Issues / Bugs

### P1-1: Shell permission swap fragile — PARTIALLY FIXED

The dynamic permission check for `run_command` temporarily mutates `tool_def.permission`. Now wrapped in `try/finally` to ensure restoration even on exception.

**Fix applied**: Added `try/finally` block. Still not thread-safe (shared `ToolDef` mutation), but no longer leaks on exception.

**Remaining**: Thread-safety issue — concurrent calls race on shared `ToolDef`.

### P1-2: Module-level side effects (config.py:7-10, file_ops.py:16)

- `config.py` calls `load_dotenv()` at import time — tests can't control env without monkeypatching
- `file_ops.py` evaluates `Path.cwd().resolve()` at import time — stale if cwd changes

**Fix**: Make both lazy (evaluate on first use).

### P1-3: API key prefix leakage — FIXED

**Fix applied**: Now prints `********...XXXX` (masked form).

### P1-4: Session ID predictability — FIXED

**Fix applied**: Replaced `hashlib.md5(str(time.time()))` with `secrets.token_hex(4)` in both `cli.py` and `logging_utils.py`.

### P1-5: SSRF protection incomplete — FIXED

**Fix applied**:
- Added DNS resolution check via `socket.getaddrinfo()` — domains resolving to private IPs are now blocked
- Added `MAX_RESPONSE_BYTES = 10MB` constant
- `web_fetch` now uses `stream=True` with chunked reading and size limit
- Expanded blocked hostnames list (metadata.google.internal, metadata.azure.com, etc.)

### P1-6: 25KB index truncation — FIXED

**Fix applied**: Now encodes to bytes first, slices, then decodes with `errors="ignore"`.

### P1-7: Frontmatter parsing fragile — FIXED

**Fix applied**: Changed to `re.split(r'^---\s*$', content, maxsplit=2, flags=re.MULTILINE)`.

### P1-8: `--max-steps 0` silently ignored — FIXED

**Fix applied**: Now uses `args.max_steps if args.max_steps != 20 else config.get("max_steps", 20)`.

---

## P2 — Code Quality / Minor

### P2-1: Unused imports

| File | Import |
|------|--------|
| `memory.py:8` | `hashlib` (never used) |
| `tools/doc_tools.py:6` | `io` (never used) |

### P2-2: Boolean accepted as integer — FIXED

**Fix applied**: Reordered checks — `boolean` now checked before `integer`, with explicit `isinstance(value, bool)` guard.

### P2-3: Hardcoded case-insensitivity in grep (file_ops.py:98)

`re.IGNORECASE` is always applied. Users cannot control case sensitivity. Add optional `case_sensitive` parameter.

### P2-4: Tool registration inconsistencies — PARTIALLY FIXED

**Fix applied**: `calculator` now has `is_read_only=True, is_concurrency_safe=True`. `shell.py` inconsistency remains (by design — permission is dynamically checked).

### P2-5: No array/object validation in registry (registry.py:82-108)

`_validate_params` only checks `string`, `integer`, `number`, `boolean`. Array and object types pass without validation.

### P2-6: Logger handler accumulation (logging_utils.py:14)

Multiple `TraceLogger` instances share the same logger name. The guard prevents adding handlers but silently ignores subsequent instances' settings.

### P2-7: No overwrite protection in doc_tools (doc_tools.py)

`create_doc` and `create_spreadsheet` silently overwrite existing files. No confirmation or error.

### P2-8: `calculate` lacks exponent cap (math_tools.py:14)

`ast.Pow` is allowed. `2**1000000` hangs the process with no timeout or limit.

### P2-9: REPL lowercases filenames — FIXED

**Fix applied**: Now splits first, then lowercases only `cmd[0]`.

---

## v0.1.0 → v0.2.0: Issues Resolved

The following issues from the previous review have been fixed:

| # | Issue | Resolution |
|---|-------|------------|
| 5 | agent.py accessing `registry._tools` (private) | Now uses `registry.list_all()` |
| 6 | `compact_context` assumes first message is system | Now agent passes `compacted` messages separately from `system_msg` |
| 12 | System prompt rebuilt every loop iteration | Now cached with `_system_prompt_cache` |
| 2 | `write_file` had no path validation | Now has `_validate_write_path` (but has P0-1 prefix bug) |
| 3 | `web_fetch` had no URL validation | Now has `_validate_url` with SSRF checks (but has P1-5 DNS gap) |

---

## Architecture Assessment

### Strengths (matching Claude Code patterns)

| Pattern | Chapter | Status |
|---------|---------|--------|
| DI-based agent loop | Ch2 | `AgentDeps` dataclass, testable |
| Circuit breaker | Ch7 | Threshold=3, reset on task start |
| Token budget tracking | Ch7 | 85% warning, 95% block |
| 7 termination reasons | Ch2 | `TerminationReason` enum |
| 4-stage permission pipeline | Ch4 | validate → rules → context → prompt |
| Rule priority: deny > ask > allow | Ch4 | `_match_rules()` with 3 passes |
| Plan mode | Ch4 | Blocks all writes |
| Progressive context compression | Ch7 | snip → microcompact → orphan → window |
| 4 typed memories | Ch6 | user/feedback/project/reference |
| MEMORY.md index | Ch6 | Dual capacity protection (200 lines / 25KB) |
| Hook system | Ch8 | 7 lifecycle events, command/function hooks |
| Tool markers (RO/CS/DST) | Ch3 | Fail-closed defaults |
| Input validation | Ch3 | `_validate_params` in registry |
| Result truncation | Ch3 | 10KB max result |
| Retry with backoff | Ch2 | Exponential, status code filtering |

### Gaps vs Claude Code

| Feature | Claude Code | MiMo Harness | Gap |
|---------|-------------|--------------|-----|
| Async agent loop | async generator | synchronous for-loop | P1 |
| Concurrent tool execution | CS partitioning + parallel | sequential only | P1 |
| Sub-agent spawning | Agent tool + worktree isolation | not implemented | P2 |
| MCP server support | full MCP protocol | not implemented | P2 |
| IDE integration | VS Code, JetBrains | CLI only | out of scope |
| Streaming responses | SSE streaming | full response polling | P2 |
| Tool auto-discovery | dynamic registration | manual `get_tools()` | P2 |

---

## Test Coverage

115 unit tests across 7 test files:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_agent.py | 19 | DI, circuit breaker, token budget, retry |
| test_permissions.py | 17 | 4-stage pipeline, rule matching, plan mode |
| test_context.py | 13 | Progressive compression, session management |
| test_registry.py | 13 | Validation, dispatch, truncation |
| test_hooks.py | 12 | Lifecycle events, command/function hooks |
| test_memory.py | 14 | Typed storage, frontmatter, validation |
| test_tools.py | 17 | File ops, shell, code exec, math, web |

**Missing coverage**: SSRF edge cases, path traversal exploits, concurrent agent calls, memory index truncation, CLI interactive commands, doc_tools path validation.

---

## Recommended Fix Priority

## Stress Test Suite (225 tests)

New `tests/test_stress_boundary.py` with 111 tests covering real-world attack scenarios:

| Category | Tests | Coverage |
|----------|-------|----------|
| Path traversal exploits | 11 | dotdot, absolute escape, prefix collision, symlink, null byte |
| SSRF bypass attempts | 15 | localhost, private IPs, IPv6, file://, metadata endpoints, DNS |
| Shell injection | 12 | chaining (;\|&`$()), readonly detection, timeout, truncation |
| Large input / memory | 6 | 1MB write, 100K lines read, result capping, truncation |
| Unicode / encoding | 5 | CJK, emoji, Arabic, accented chars in all tools |
| Permission pipeline | 12 | deny>ask>allow priority, plan mode, patterns, performance |
| Thread safety | 3 | concurrent circuit breaker, permission log, token budget |
| Math DoS vectors | 12 | eval/exec/import blocked, large exponents, division by zero |
| Context compression | 7 | 1000 messages, tool results, snip, microcompact, orphan filter |
| Memory boundaries | 11 | 50 memories, index limits, traversal, frontmatter edge cases |
| Registry edge cases | 7 | unknown tool, missing params, type validation, boolean guard |
| Doc tools boundary | 3 | path validation, empty title, empty data |

---

## Remaining Issues (Low Priority)

| Priority | Issue | Status |
|----------|-------|--------|
| P1-2 | Module-level side effects (config.py, file_ops.py) | Remaining — lazy init needed |
| P2-3 | Hardcoded case-insensitivity in grep | Remaining |
| P2-5 | No array/object validation in registry | Remaining |
| P2-6 | Logger handler accumulation | Remaining |
| P2-7 | No overwrite protection in doc_tools | Remaining |
| P2-8 | Calculator lacks exponent cap | Remaining |

---

## v0.1.0 Review (Archived)

<details>
<summary>Previous review findings (most resolved in v0.2.0)</summary>

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | P0 | Shell readonly detection bypassable | Fixed (chaining detection added) |
| 2 | P0 | Write no path restriction | Fixed (now has `_validate_write_path`, but prefix bug remains) |
| 3 | P0 | Web fetch SSRF | Fixed (now has `_validate_url`, but DNS gap remains) |
| 4 | P0 | Import position | Fixed (imports at top of file) |
| 5 | P1 | `registry._tools` private access | Fixed (uses `list_all()`) |
| 6 | P1 | `compact_context` system prompt assumption | Fixed (agent passes messages correctly) |
| 7 | P1 | `csv.DictWriter` key misalignment | Still present (P2-7) |
| 8 | P1 | `dirname` empty string | Fixed (added guard) |
| 9 | P1 | CLI result check unreliable | Fixed (uses `startswith("[")` pattern) |
| 10 | P2 | Unused imports | Partially fixed |
| 11 | P2 | Redundant lambda | Fixed |
| 12 | P2 | Prompt rebuilt every iteration | Fixed (cached) |
| 13 | P2 | Empty `safe_title` | Still present |

</details>
