"""Context management - progressive compression following Claude Code architecture.

Implements Ch7 patterns:
- Four-level progressive compression (snip → microcompact → collapse → autocompact)
- Circuit breaker for compression failures
- Compact boundary messages
- Token budget tracking
- Message chain continuity preservation
"""

import os
import re
import glob as _glob
import json
import time
import shutil
import platform
from dataclasses import dataclass, field
from typing import Optional, Any


# ---------------------------------------------------------------------------
# Constants (Ch7: compression thresholds — Claude Code style)
# ---------------------------------------------------------------------------
CONTEXT_WINDOW_TOKENS = 200_000          # Total context window (200K)
STARTUP_RESERVE_TOKENS = 10_000          # System prompt + memory + AGENTS.md (~7.5K)
COMPRESS_TRIGGER_RATIO = 0.85            # Trigger compression at 85% of window

SNIP_MAX_AGE_MESSAGES = 20  # Messages older than this get snipped
MICROCOMPACT_KEEP_RECENT = 5  # Keep last N tool results in microcompact
COMPRESS_MARKER = "[Old tool result content cleared]"
COMPACT_INSTRUCTIONS_KEY = "__compact_instructions__"

# Compression triggers when conversation reaches this many tokens
COMPRESS_TRIGGER_TOKENS = int(CONTEXT_WINDOW_TOKENS * COMPRESS_TRIGGER_RATIO)


# ---------------------------------------------------------------------------
# Session dataclass
# ---------------------------------------------------------------------------
@dataclass
class Session:
    session_id: str
    messages: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    working_dir: str = ""
    compaction_count: int = 0
    auto_save_dir: str = ""
    name: str = ""

    def add_message(self, role: str, content, **kwargs):
        msg = {"role": role, "content": content}
        msg.update(kwargs)
        self.messages.append(msg)
        if self.auto_save_dir:
            self.auto_save()

    def get_messages(self) -> list:
        return self.messages

    def auto_save(self):
        """Append the latest message as a JSONL line to the session file."""
        if not self.auto_save_dir or not self.messages:
            return
        os.makedirs(self.auto_save_dir, exist_ok=True)
        path = os.path.join(self.auto_save_dir, f"{self.session_id}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.messages[-1], ensure_ascii=False) + "\n")

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.session_id,
                "messages": self.messages,
                "created_at": self.created_at,
                "working_dir": self.working_dir,
                "compaction_count": self.compaction_count,
                "name": self.name,
            }, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "Session":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            session_id=data["session_id"],
            messages=data.get("messages", []),
            created_at=data.get("created_at", time.time()),
            working_dir=data.get("working_dir", ""),
            compaction_count=data.get("compaction_count", 0),
            name=data.get("name", ""),
        )

    @classmethod
    def from_jsonl(cls, path: str) -> "Session":
        """Reconstruct a Session from a JSONL file (one message per line)."""
        messages = []
        created_at = os.path.getmtime(path)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    messages.append(json.loads(line))
        session_id = os.path.splitext(os.path.basename(path))[0]
        return cls(
            session_id=session_id,
            messages=messages,
            created_at=created_at,
        )


# ---------------------------------------------------------------------------
# Session checkpoints (S12: snapshot & rewind)
# ---------------------------------------------------------------------------
class CheckpointManager:
    """Manages file snapshots for session-level undo/rewind."""

    def __init__(self, session_id: str):
        self.checkpoint_dir = os.path.join(".mimo", "checkpoints", session_id)
        self._seq = 0
        self._batch_dir: Optional[str] = None

    def snapshot(self, file_path: str) -> str:
        """H3: Save a copy of file before edit using relative path to avoid collisions."""
        self._seq += 1
        dest_dir = os.path.join(self.checkpoint_dir, str(self._seq))
        os.makedirs(dest_dir, exist_ok=True)
        # H3: Use sanitized relative path to avoid cross-directory collisions
        abs_path = os.path.abspath(file_path)
        try:
            rel = os.path.relpath(abs_path, os.getcwd())
        except ValueError:
            rel = os.path.basename(file_path)
        safe_name = rel.replace(os.sep, "__").replace("/", "__")
        dest = os.path.join(dest_dir, safe_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(file_path, dest)
        # Store original path metadata for accurate restoration
        import json as _json
        meta_path = os.path.join(dest_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            _json.dump({"original_path": abs_path, "safe_name": safe_name}, f)
        return dest

    def restore_last(self) -> list[str]:
        """Restore all files from the latest checkpoint. Returns list of restored paths."""
        if self._seq == 0:
            return []
        checkpoint_path = os.path.join(self.checkpoint_dir, str(self._seq))
        if not os.path.isdir(checkpoint_path):
            return []
        restored = []
        # Load metadata if available
        meta_path = os.path.join(checkpoint_path, "meta.json")
        original_path = None
        if os.path.exists(meta_path):
            import json as _json
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = _json.load(f)
                original_path = meta.get("original_path")
        for filename in os.listdir(checkpoint_path):
            if filename == "meta.json":
                continue
            src = os.path.join(checkpoint_path, filename)
            if os.path.isfile(src):
                # Restore to original path if available, else cwd
                if original_path:
                    dest = original_path
                else:
                    dest = os.path.join(os.getcwd(), filename)
                os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
                shutil.copy2(src, dest)
                restored.append(dest)
        self._seq -= 1
        return restored

    # -- Batch support (X2: Multi-File Checkpoint Batch) --

    def begin_batch(self) -> str:
        """Start a new batch checkpoint. Returns the batch directory path."""
        self._seq += 1
        self._batch_dir = os.path.join(self.checkpoint_dir, str(self._seq))
        os.makedirs(self._batch_dir, exist_ok=True)
        return self._batch_dir

    def snapshot_to_batch(self, file_path: str) -> str:
        """Save a file snapshot into the current batch directory."""
        if not self._batch_dir:
            raise RuntimeError("No active batch. Call begin_batch() first.")
        abs_path = os.path.abspath(file_path)
        try:
            rel = os.path.relpath(abs_path, os.getcwd())
        except ValueError:
            rel = os.path.basename(file_path)
        safe_name = rel.replace(os.sep, "__").replace("/", "__")
        dest = os.path.join(self._batch_dir, safe_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(file_path, dest)
        # Store metadata
        meta_path = os.path.join(self._batch_dir, "meta.json")
        import json as _json
        with open(meta_path, "w", encoding="utf-8") as f:
            _json.dump({"original_path": abs_path, "safe_name": safe_name}, f)
        return dest

    def end_batch(self):
        """Finalize the current batch."""
        self._batch_dir = None


# ---------------------------------------------------------------------------
# Level 1: Snip compression (Ch7: lightest, no LLM)
# ---------------------------------------------------------------------------
def snip_compress(messages: list, max_age: int = SNIP_MAX_AGE_MESSAGES) -> list:
    """Level 1: Replace old tool results with markers.

    Why markers instead of deletion? Deleting messages breaks the
    message chain — subsequent messages may reference earlier tool_call_ids.
    """
    if len(messages) <= max_age:
        return messages

    result = []
    cutoff = len(messages) - max_age
    for i, msg in enumerate(messages):
        if i < cutoff and isinstance(msg, dict) and msg.get("role") == "tool":
            # Snip: replace content with marker, preserve structure
            snipped = dict(msg)
            snipped["content"] = COMPRESS_MARKER
            result.append(snipped)
        else:
            result.append(msg)
    return result


# ---------------------------------------------------------------------------
# Level 2: Microcompact (Ch7: time-triggered, keep recent N tool results)
# ---------------------------------------------------------------------------
def microcompact(
    messages: list, keep_recent: int = MICROCOMPACT_KEEP_RECENT
) -> list:
    """Level 2: Keep only the most recent N tool results, clear the rest.

    Compressible tool types: any message with role="tool".
    """
    # Find indices of tool result messages
    tool_indices = [
        i for i, m in enumerate(messages)
        if isinstance(m, dict) and m.get("role") == "tool"
    ]

    if len(tool_indices) <= keep_recent:
        return messages

    # Indices to compress (all except the most recent N)
    compress_indices = set(tool_indices[:-keep_recent])

    result = []
    for i, msg in enumerate(messages):
        if i in compress_indices:
            compressed = dict(msg)
            compressed["content"] = COMPRESS_MARKER
            result.append(compressed)
        else:
            result.append(msg)
    return result


# ---------------------------------------------------------------------------
# Level 3: LLM-based semantic compression (Ch7: model-driven summarization)
# ---------------------------------------------------------------------------
SUMMARIZATION_PROMPT = """You are a conversation summarizer. Produce a structured summary of this conversation.

The summary MUST include:
1. User's stated goals and current progress
2. Key technical decisions made
3. Files examined or modified (with important code snippets)
4. Errors encountered and how they were fixed
5. Pending tasks and next steps

Rules:
- Preserve file paths, function names, error messages exactly
- Preserve code snippets that were discussed or modified
- Preserve any project instructions, coding conventions, or rules mentioned in the conversation
- Use bullet points for clarity
- Do NOT include tool call IDs or internal metadata
- Do NOT fabricate information not in the conversation
- Maximum length: 500 words

Conversation to summarize:
{conversation_text}

Produce the summary now:"""


def llm_compress(
    messages: list,
    client,
    model: str = "mimo-v2.5-pro",
    max_summary_tokens: int = 2048,
) -> list | None:
    """Level 3: LLM-based semantic compression (Claude Code style).

    Replaces the ENTIRE conversation with a single structured summary.
    No messages are kept — the summary is the conversation.

    Returns: [summary_message] or None on failure (caller falls back).
    """
    if len(messages) <= 1:
        return messages

    # Format all messages for summarization
    parts = []
    total_chars = 0
    max_chars = 60000  # ~15K tokens of input
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if not isinstance(content, str):
            content = str(content) if content else ""
        # Truncate individual long messages (e.g. large tool results)
        if len(content) > 3000:
            content = content[:3000] + "... [truncated]"
        line = f"[{role}]: {content}"
        if total_chars + len(line) > max_chars:
            parts.append(f"[{role}]: ... [remaining messages omitted]")
            break
        parts.append(line)
        total_chars += len(line)

    conversation_text = "\n".join(parts)
    prompt = SUMMARIZATION_PROMPT.format(conversation_text=conversation_text)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=max_summary_tokens,
            temperature=0.3,
        )
        summary = response.choices[0].message.content
        if not summary or not summary.strip():
            return None
        return [
            {"role": "assistant", "content": "[Conversation Summary]\n" + summary.strip()}
        ]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Orphan tool result filter (prevents sending unmatched tool results)
# ---------------------------------------------------------------------------
def _filter_orphan_tool_results(messages: list) -> list:
    """Remove tool results that don't have matching tool_calls in the window."""
    # Collect valid tool_call_ids from assistant messages
    valid_ids = set()
    for msg in messages:
        if isinstance(msg, dict):
            for tc in (msg.get("tool_calls") or []):
                tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                if tc_id:
                    valid_ids.add(tc_id)

    result = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "tool":
            tc_id = msg.get("tool_call_id")
            if tc_id in valid_ids:
                result.append(msg)
            # else: orphan, skip
        else:
            result.append(msg)
    return result


# ---------------------------------------------------------------------------
# Main compaction entry point (Ch7: progressive compression)
# ---------------------------------------------------------------------------
def estimate_tokens(messages: list) -> int:
    """Estimate token count for a message list (~4 chars per token)."""
    total_chars = sum(
        len(json.dumps(m, ensure_ascii=False)) if isinstance(m, dict)
        else len(str(m))
        for m in messages
    )
    return total_chars // 4


def _extract_instructions(messages: list) -> list:
    """Extract system messages containing project instructions (A9)."""
    instructions = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "system":
            content = msg.get("content", "")
            if isinstance(content, str) and ("Project Memory" in content
                                             or "instructions" in content.lower()
                                             or "rules" in content.lower()):
                instructions.append(dict(msg))
    return instructions


def compact_context(
    messages: list,
    max_messages: int = 0,
    client=None,
    model: str = "",
    estimated_tokens: int = 0,
    compaction_attempts: int = 0,
    compaction_failures: int = 0,
) -> tuple[list, int, int, bool]:
    """Context compression (Claude Code style).

    After compression, conversation is replaced with a single summary
    (~12% of original tokens, capped at ~15K). This frees up ~170K+
    tokens for continued work.

    Args:
        messages: conversation messages
        max_messages: legacy message-count limit (0 = auto)
        client: OpenAI-compatible client for LLM compression
        model: model name for LLM compression
        estimated_tokens: pre-computed token count (avoids re-estimation)
        compaction_attempts: running count of compaction attempts
        compaction_failures: running count of compaction failures

    Returns:
        (compacted_messages, attempts, failures, thrashing_detected)
    """
    # Estimate tokens if not provided
    tokens = estimated_tokens if estimated_tokens > 0 else estimate_tokens(messages)

    # Check if compression is needed
    needs_token_compress = tokens >= COMPRESS_TRIGGER_TOKENS
    needs_message_compress = max_messages > 0 and len(messages) > max_messages

    if not needs_token_compress and not needs_message_compress:
        return _filter_orphan_tool_results(messages), compaction_attempts, compaction_failures, False

    # A9: Extract instructions before compression so we can re-insert them
    preserved_instructions = _extract_instructions(messages)

    # Case 1: Token-based compression (Claude Code style — aggressive)
    if needs_token_compress:
        # A8: Check if thrashing is detected (3 consecutive failures)
        if compaction_failures >= 3:
            result = _filter_orphan_tool_results(messages)
            return result, compaction_attempts, compaction_failures, True

        # Level 3: LLM-based semantic compression (preferred)
        if client is not None:
            llm_result = llm_compress(messages, client, model or "mimo-v2.5-pro")
            if llm_result is not None:
                # A8: Check if compression achieved at least 30% reduction
                new_tokens = estimate_tokens(llm_result)
                if tokens > 0 and (tokens - new_tokens) / tokens < 0.30:
                    compaction_failures += 1
                else:
                    compaction_failures = 0
                compaction_attempts += 1
                # A9: Re-insert preserved instructions
                for instr in reversed(preserved_instructions):
                    llm_result.insert(0, instr)
                return llm_result, compaction_attempts, compaction_failures, False
            # LLM failed, fall through to truncation
            compaction_failures += 1
            compaction_attempts += 1

        # Fallback: aggressive truncation — system marker + last 2 messages
        result = []
        result.append({
            "role": "system",
            "content": f"[Context compacted: {len(messages)} messages, ~{tokens} tokens reduced to this summary]"
        })
        recent = messages[-2:] if len(messages) >= 2 else messages
        for msg in recent:
            if isinstance(msg, dict):
                content = msg.get("content", "")
                if isinstance(content, str) and len(content) > 2000:
                    msg = dict(msg)
                    msg["content"] = content[:2000] + "... [truncated]"
                result.append(msg)
        # A9: Re-insert preserved instructions
        for instr in reversed(preserved_instructions):
            result.insert(0, instr)
        return _filter_orphan_tool_results(result), compaction_attempts, compaction_failures, False

    # Case 2: Message-count limit (legacy, simple trim)
    result = _filter_orphan_tool_results(messages[-max_messages:])
    return result, compaction_attempts, compaction_failures, False


# ---------------------------------------------------------------------------
# Compact boundary message (Ch7: metadata marker)
# ---------------------------------------------------------------------------
def make_compact_boundary(
    pre_tokens: int, pre_messages: int, trigger: str = "auto"
) -> dict:
    """Create a compact boundary message with compression metadata."""
    return {
        "role": "system",
        "content": (
            f"[Context compacted: {pre_messages} messages → "
            f"{pre_tokens} tokens, trigger={trigger}]"
        ),
        "compact_metadata": {
            "trigger": trigger,
            "pre_tokens": pre_tokens,
            "pre_messages": pre_messages,
            "timestamp": time.time(),
        },
    }


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------
def build_system_prompt(tools_desc: str, memory_content: str = "") -> str:
    """Assemble dynamic system prompt with environment context."""
    cwd = os.getcwd()
    env_info = f"{platform.system()} {platform.release()}"

    prompt = f"""You are MiMo Harness, a capable AI assistant powered by Xiaomi MiMo model.

## Environment
- Working directory: {cwd}
- Platform: {env_info}
- Python: {platform.python_version()}

## Capabilities
You can help with:
- File operations (read, write, edit, search)
- Code writing and execution
- Web search and content fetching
- Document creation (markdown, CSV)
- Mathematical calculations
- Shell command execution

## Rules
- Use absolute file paths
- Ask for confirmation before write/deploy operations
- Explain what you're doing before using tools
- Be concise but thorough
- If a task is ambiguous, ask for clarification
- When a tool fails, analyze the error and try a different approach

## Available Tools
{tools_desc}"""

    if memory_content:
        prompt += f"\n\n## Project Memory\n{memory_content}"

    return prompt


# ---------------------------------------------------------------------------
# Memory loader (Ch6: MEMORY.md, CLAUDE.md, .mimo/memory.md)
# ---------------------------------------------------------------------------
_IMPORT_PATTERN = re.compile(r"@([\w./\\-]+)")


def _resolve_imports(content: str, base_dir: str, depth: int = 0) -> str:
    """Resolve @import directives in content (A6).

    Scans for @path/to/file patterns and inlines the referenced file content.
    Limits to 5 levels of nesting to prevent infinite loops.
    """
    if depth >= 5:
        return content

    def _replace_import(match):
        rel_path = match.group(1)
        abs_path = os.path.normpath(os.path.join(base_dir, rel_path))
        # Security: ensure resolved path stays within base_dir
        base_abs = os.path.normpath(os.path.abspath(base_dir))
        try:
            resolved = os.path.abspath(abs_path)
        except (ValueError, OSError):
            return match.group(0)
        if not resolved.startswith(base_abs + os.sep) and resolved != base_abs:
            return match.group(0)  # Reject path traversal
        if not os.path.exists(abs_path):
            return match.group(0)  # Leave unresolved imports as-is
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                imported = f.read()
            # Recursively resolve nested imports
            imported = _resolve_imports(imported, os.path.dirname(abs_path), depth + 1)
            return imported
        except Exception:
            return match.group(0)

    return _IMPORT_PATTERN.sub(_replace_import, content)


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse simple YAML frontmatter (--- delimited) without PyYAML dependency.

    Returns (metadata_dict, body_content).
    Only supports simple key: [value] patterns for the paths field.
    """
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    fm_block = content[3:end].strip()
    body = content[end + 3:].strip()
    meta = {}
    for line in fm_block.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            # Parse list syntax: ["*.py", "*.js"]
            if val.startswith("[") and val.endswith("]"):
                items = [
                    item.strip().strip('"').strip("'")
                    for item in val[1:-1].split(",")
                    if item.strip()
                ]
                meta[key] = items
            else:
                meta[key] = val.strip('"').strip("'")
    return meta, body


def _load_path_scoped_rules(project_dir: str) -> list[tuple[list[str], str]]:
    """Scan .mimo/rules/*.md for path-scoped rules (A5).

    Returns list of (paths_patterns, rule_content) tuples.
    """
    rules_dir = os.path.join(project_dir, ".mimo", "rules")
    if not os.path.isdir(rules_dir):
        return []
    rules = []
    for rule_file in sorted(_glob.glob(os.path.join(rules_dir, "*.md"))):
        try:
            with open(rule_file, "r", encoding="utf-8") as f:
                raw = f.read()
            meta, body = _parse_frontmatter(raw)
            if not body:
                continue
            paths = meta.get("paths", [])
            rules.append((paths, body))
        except Exception:
            pass
    return rules


def load_memory(project_dir: str, current_file: str = "") -> str:
    """Load project memory files.

    Reads MEMORY.md index, CLAUDE.md instructions, and .mimo/memory.md.
    Resolves @import directives (A6).
    Loads path-scoped rules from .mimo/rules/*.md (A5).
    Respects capacity limits: max 200 lines per file.
    """
    memory_parts = []
    for name in ["MEMORY.md", "CLAUDE.md", "AGENTS.md", ".mimo/memory.md"]:
        path = os.path.join(project_dir, name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # Ch6: dual capacity protection — 200 line limit
                if len(lines) > 200:
                    lines = lines[:200] + ["... [truncated to 200 lines]\n"]
                content = "".join(lines).strip()
                # A6: Resolve @import directives
                if content:
                    content = _resolve_imports(content, project_dir)
                if content:
                    memory_parts.append(f"### {name}\n{content}")
            except Exception:
                pass

    # A5: Load path-scoped rules from .mimo/rules/*.md
    rules = _load_path_scoped_rules(project_dir)
    if rules:
        import fnmatch
        rule_sections = []
        for paths_patterns, rule_content in rules:
            if not paths_patterns:
                # No path filter — always include
                rule_sections.append(rule_content)
            elif current_file:
                # Include only if current file matches any pattern
                for pattern in paths_patterns:
                    if fnmatch.fnmatch(current_file, pattern):
                        rule_sections.append(rule_content)
                        break
            # If current_file is empty and patterns exist, skip (context-dependent)
        if rule_sections:
            memory_parts.append("### Path-Scoped Rules\n" + "\n\n".join(rule_sections))

    return "\n\n".join(memory_parts)
