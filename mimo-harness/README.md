# MiMo Harness

A production-grade AI agent harness powered by Xiaomi MiMo model. Inspired by Claude Code's architecture, provides coding assistance, web search, document creation, and more.

> Part of the [Agent Learning Hub](https://github.com/datawhalechina/Agent-Learning-Hub) project.

## Features

- **File Operations**: Read, write, edit files; glob and grep search
- **Code Execution**: Run Python code in isolated subprocess
- **Shell Commands**: Execute shell commands with read-only auto-approval
- **Web Search**: DuckDuckGo search and URL content fetching
- **Document Creation**: Generate markdown, CSV, and text documents
- **Math Calculator**: Safe expression evaluation (no eval injection)
- **Permission System**: Three-tier access control (read/write/destructive)
- **Session Management**: Save/load conversation history
- **Structured Logging**: Trace IDs and step tracking

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

### Interactive Mode
```bash
mimo-harness
# or with options:
mimo-harness --auto-approve  # Skip confirmation prompts
mimo-harness --dry-run       # Show actions without executing
mimo-harness --verbose       # Show trace logs
```

### Commands (Interactive Mode)
| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/quit` | Exit |
| `/clear` | Clear conversation |
| `/tools` | List available tools |
| `/save <path>` | Save session |
| `/load <path>` | Load session |
| `/dry-run` | Toggle dry-run mode |
| `/auto` | Toggle auto-approve mode |

## Architecture

```
mimo_harness/
├── agent.py          # Core observe-think-act loop
├── config.py         # Environment configuration
├── permissions.py    # Three-tier permission gate
├── context.py        # Session & context management
├── logging_utils.py  # Structured logging
└── tools/
    ├── registry.py   # Tool registration & dispatch
    ├── file_ops.py   # File read/write/edit/glob/grep
    ├── shell.py      # Shell command execution
    ├── code_exec.py  # Python code execution
    ├── web_tools.py  # Web search & fetch
    ├── doc_tools.py  # Document creation
    └── math_tools.py # Safe math evaluation
```

### Agent Loop
```
User Task → System Prompt + Context → LLM (MiMo)
    ↓
Tool Call? → Permission Check → Execute → Feed Result Back → Loop
    ↓
No Tool Call → Final Response → Done
```

### Permission Model
| Level | Tools | Behavior |
|-------|-------|----------|
| READ | File read, grep, glob, search, calculator | Auto-approved |
| WRITE | File write/edit, code execution, shell commands | Requires confirmation |
| DESTRUCTIVE | (blocked by default) | Requires confirmation + warning |

## Examples

### Coding Assistant
```
You: Create a Python function to calculate prime numbers and test it
Agent: I'll create a prime number function and verify it works.
  [write_file] primes.py
  [execute_python] test code
  Result: Function works correctly, first 10 primes: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

### Web Research
```
You: Search for the latest developments in AI agents
Agent: Let me search for that.
  [web_search] "latest AI agent developments 2026"
  Here are the top results: ...
```

### Document Creation
```
You: Create a project status report in markdown
Agent: I'll create a status report template.
  [create_doc] Project_Status_Report.md
  Document created at ./Project_Status_Report.md
```

## Configuration

Create `.env` file:
```
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_API_KEY=your-api-key-here
MIMO_MODEL=mimo-v2.5-pro
```

## License

MIT License. See [LICENSE](../LICENSE) for details.
