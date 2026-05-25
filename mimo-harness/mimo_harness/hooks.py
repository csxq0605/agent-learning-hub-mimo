"""Hook system - lifecycle extension points following Claude Code architecture.

Implements Ch8 patterns:
- Lifecycle events: PreToolUse, PostToolUse, Stop, SessionStart/End
- Command hooks with matcher patterns
- Hook response protocol (decision/updatedInput/additionalContext)
- Priority ordering and timeout management
"""

import json
import subprocess
import platform
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable


class HookEvent(Enum):
    """Lifecycle events (Ch8: 26 events, we implement the core ones)."""
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    POST_TOOL_USE_FAILURE = "PostToolUseFailure"
    STOP = "Stop"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    PRE_COMPACT = "PreCompact"
    POST_COMPACT = "PostCompact"
    TASK_CREATED = "TaskCreated"
    TASK_COMPLETED = "TaskCompleted"
    SUBAGENT_START = "SubagentStart"
    SUBAGENT_STOP = "SubagentStop"
    PERMISSION_REQUEST = "PermissionRequest"
    PERMISSION_DENIED = "PermissionDenied"
    CONFIG_CHANGE = "ConfigChange"
    CWD_CHANGED = "CwdChanged"
    FILE_CHANGED = "FileChanged"


class HookDecision(Enum):
    """Hook response decisions (Ch8: approve/block)."""
    APPROVE = "approve"
    BLOCK = "block"


@dataclass
class HookResult:
    """Structured hook response (Ch8: decision/updatedInput/additionalContext)."""
    decision: HookDecision = HookDecision.APPROVE
    reason: str = ""
    additional_context: str = ""
    updated_input: Optional[dict] = None

    @property
    def is_blocking(self) -> bool:
        return self.decision == HookDecision.BLOCK


@dataclass
class HookConfig:
    """Configuration for a single hook."""
    event: HookEvent
    matcher: str = "*"        # Tool name pattern to match
    command: str = ""         # Shell command to execute
    timeout: float = 10.0     # Timeout in seconds (Ch8: < 1s recommended for sync)
    async_mode: bool = False  # Ch8: async hooks don't block

    def matches(self, tool_name: str) -> bool:
        """Check if this hook matches a tool name."""
        if self.matcher == "*":
            return True
        if self.matcher.endswith("*"):
            return tool_name.startswith(self.matcher[:-1])
        return self.matcher == tool_name


class HookRunner:
    """Execute hooks for lifecycle events (Ch8: Observer + Chain of Responsibility).

    Priority ordering (Ch8):
    1. userSettings (highest)
    2. projectSettings
    3. localSettings
    4. builtinHook (lowest)
    """

    def __init__(self):
        self._hooks: dict[HookEvent, list[HookConfig]] = {}
        self._function_hooks: dict[HookEvent, list[Callable]] = {}
        self.enabled = True

    def register(self, config: HookConfig):
        """Register a command hook for an event."""
        if config.event not in self._hooks:
            self._hooks[config.event] = []
        self._hooks[config.event].append(config)

    def register_function(self, event: HookEvent, fn: Callable):
        """Register an in-memory function hook (Ch8: Function Hook type)."""
        if event not in self._function_hooks:
            self._function_hooks[event] = []
        self._function_hooks[event].append(fn)

    def register_many(self, configs: list[HookConfig]):
        for c in configs:
            self.register(c)

    def run_hooks(
        self,
        event: HookEvent,
        tool_name: str = "",
        tool_input: dict = None,
        tool_result: str = "",
    ) -> HookResult:
        """Run all matching hooks for an event (Ch8: Chain of Responsibility).

        Returns the first blocking result, or approve if all pass.
        """
        if not self.enabled:
            return HookResult()

        # Run function hooks first (in-memory, fastest)
        for fn in self._function_hooks.get(event, []):
            try:
                result = fn(tool_name=tool_name, tool_input=tool_input, tool_result=tool_result)
                if isinstance(result, HookResult) and result.is_blocking:
                    return result
            except Exception:
                pass  # Ch8: hooks are advisors, not commanders

        # Run command hooks
        for config in self._hooks.get(event, []):
            if not config.matches(tool_name):
                continue

            if config.async_mode:
                # Ch8: async hooks run in background, don't block
                self._run_async(config, tool_name, tool_input, tool_result)
                continue

            result = self._run_command_hook(config, tool_name, tool_input, tool_result)
            if result.is_blocking:
                return result

        return HookResult()

    def _run_command_hook(
        self,
        config: HookConfig,
        tool_name: str,
        tool_input: dict = None,
        tool_result: str = "",
    ) -> HookResult:
        """Execute a single command hook with timeout."""
        # Build hook input (Ch8: structured JSON input)
        hook_input = json.dumps({
            "event": config.event.value,
            "tool_name": tool_name,
            "tool_input": tool_input or {},
            "tool_result": tool_result[:500],  # Truncate for hook input
        }, ensure_ascii=False)

        try:
            # Ch8: command hooks execute via subprocess
            if platform.system() == "Windows":
                result = subprocess.run(
                    config.command,
                    shell=True,
                    input=hook_input,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout,
                    encoding="utf-8",
                    errors="replace",
                )
            else:
                result = subprocess.run(
                    config.command,
                    shell=True,
                    input=hook_input,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout,
                )

            # Ch8: exit code semantics
            # 0 = pass, 2 = block, other = warning
            if result.returncode == 2:
                return HookResult(
                    decision=HookDecision.BLOCK,
                    reason=result.stderr.strip() if result.stderr else "Blocked by hook",
                )

            # Parse JSON response from stdout (Ch8: hook response protocol)
            if result.stdout.strip():
                try:
                    response = json.loads(result.stdout.strip())
                    decision = response.get("decision", "approve")
                    if decision == "block":
                        return HookResult(
                            decision=HookDecision.BLOCK,
                            reason=response.get("reason", "Blocked by hook"),
                        )
                    return HookResult(
                        decision=HookDecision.APPROVE,
                        additional_context=response.get("additionalContext", ""),
                        updated_input=response.get("updatedInput"),
                    )
                except json.JSONDecodeError:
                    pass  # Non-JSON stdout is treated as approve

            if result.returncode != 0 and result.returncode != 2:
                # Non-zero, non-2 exit code: warning but continue
                return HookResult()

        except subprocess.TimeoutExpired:
            # Ch8: timeout = error, not block
            return HookResult()
        except Exception:
            pass

        return HookResult()

    def _run_async(
        self,
        config: HookConfig,
        tool_name: str,
        tool_input: dict = None,
        tool_result: str = "",
    ):
        """Run a hook asynchronously (fire-and-forget)."""
        hook_input = json.dumps({
            "event": config.event.value,
            "tool_name": tool_name,
            "tool_input": tool_input or {},
            "tool_result": tool_result[:500],
        }, ensure_ascii=False)

        try:
            proc = subprocess.Popen(
                config.command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Write hook input to stdin and close the pipe so the
            # subprocess does not hang waiting for EOF.
            try:
                proc.stdin.write(hook_input.encode("utf-8"))
                proc.stdin.close()
            except Exception:
                pass  # If stdin write fails, let the process continue
        except Exception:
            pass  # Async hooks are fire-and-forget

    def load_from_config(self, config: dict):
        """Load hooks from a configuration dictionary.

        Expected format (Ch8):
        {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "validate.sh", "timeout": 5}
                        ]
                    }
                ]
            }
        }
        """
        hooks_config = config.get("hooks", {})
        for event_name, matchers in hooks_config.items():
            try:
                event = HookEvent(event_name)
            except ValueError:
                continue

            for matcher_config in matchers:
                matcher = matcher_config.get("matcher", "*")
                for hook_def in matcher_config.get("hooks", []):
                    if hook_def.get("type") == "command":
                        self.register(HookConfig(
                            event=event,
                            matcher=matcher,
                            command=hook_def.get("command", ""),
                            timeout=hook_def.get("timeout", 10.0),
                            async_mode=hook_def.get("async", False),
                        ))
