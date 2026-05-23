# Stage 3: Agent Harness Analysis

## System Studied: Claude Code

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Agent Harness                  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   Tool   │  │Permission│  │   Session    │  │
│  │ Registry │  │   Gate   │  │   Store      │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │               │           │
│       v              v               v           │
│  ┌──────────────────────────────────────────┐   │
│  │            Agent Loop (LLM)              │   │
│  │  observe -> think -> act -> observe      │   │
│  └──────────────────────────────────────────┘   │
│       │                                          │
│       v                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Context  │  │  Hooks   │  │  Sub-agents  │  │
│  │Compaction│  │(pre/post)│  │  (parallel)  │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
```

### Key Components

| Component | Claude Code | Our Demo |
|-----------|------------|----------|
| **Tool Registry** | 20+ tools (Read, Edit, Bash, Glob, Grep, Agent...) | 4 tools (read, write, run, list) |
| **Permission Gate** | Auto/Ask/Deny per tool per mode | Permission enum with auto/approve/block |
| **Session Store** | JSONL transcripts, cross-surface sessions | In-memory session with message history |
| **Context Compaction** | Auto-summarize when approaching limits | Keep first + last N messages |
| **Hooks** | Shell commands pre/post tool execution | Not implemented (would be event emitter) |
| **Sub-agents** | Independent context windows, parallel execution | Not implemented (would be Agent class) |
| **MCP** | External tool servers via protocol | Not implemented |

### What I Learned

1. **The harness is the product, not the model.** Claude Code's power comes from its tool design, permission system, and context management -- not just from Claude's capabilities.

2. **Tool design is critical.** Anthropic spent more time optimizing SWE-bench tools than on the overall prompt. The Agent-Computer Interface (ACI) matters as much as the model.

3. **Context compaction is essential.** Without it, long conversations hit context limits. Claude Code auto-summarizes older messages.

4. **Permission gates prevent disasters.** Destructive operations (delete, force push) should be blocked by default. Write operations should prompt for confirmation.

5. **Sub-agents save context.** By delegating research to a sub-agent, the main conversation stays focused. Each sub-agent has its own context window.

6. **Hooks enable automation.** Auto-format on save, lint before commit -- hooks turn the agent into a proper development workflow.

## Deliverable

A working harness demo (`harness_demo.py`) with:
- Pluggable tool registry
- Permission gate with 4 levels
- Session store
- Context compaction
- Agent loop with max steps

## How to Run
```bash
export ANTHROPIC_API_KEY=your-key
pip install anthropic
python harness_demo.py
```

## References
- [Claude Code Overview](https://code.claude.com/docs/en/overview)
- [Claude Code Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)
- [Dive into Claude Code](https://arxiv.org/abs/2604.14228)
