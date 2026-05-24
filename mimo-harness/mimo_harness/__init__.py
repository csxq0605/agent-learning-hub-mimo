"""MiMo Harness - A production-grade AI agent harness powered by Xiaomi MiMo model.

Architecture follows Claude Code patterns:
- Ch2: Dependency injection, circuit breaker, state machine
- Ch3: Fail-closed tool defaults, concurrency markers, input validation
- Ch4: 4-stage permission pipeline, rule-based matching
- Ch6: Typed memory system, MEMORY.md index
- Ch7: Progressive context compression, token budget
- Ch8: Hook system with lifecycle events
"""

__version__ = "0.2.0"

from .agent import MiMoHarness, AgentDeps, CircuitBreaker, TokenBudget
from .permissions import PermissionGate, Permission, PermissionMode, PermissionRule
from .context import Session, compact_context, load_memory
from .hooks import HookRunner, HookConfig, HookEvent, HookResult, HookDecision
from .memory import MemoryStore, MemoryType, MemoryEntry
from .logging_utils import TraceLogger

__all__ = [
    "MiMoHarness",
    "AgentDeps",
    "CircuitBreaker",
    "TokenBudget",
    "PermissionGate",
    "Permission",
    "PermissionMode",
    "PermissionRule",
    "Session",
    "compact_context",
    "load_memory",
    "HookRunner",
    "HookConfig",
    "HookEvent",
    "HookResult",
    "HookDecision",
    "MemoryStore",
    "MemoryType",
    "MemoryEntry",
    "TraceLogger",
]
