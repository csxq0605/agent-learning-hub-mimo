# DevOps Agent

A production-ready agent for system health checks, log analysis, and deployment management.

## User
DevOps engineers and SREs who need quick system diagnostics and log analysis.

## Task
- Check system health (CPU, memory, processes)
- Analyze log files for errors and patterns
- Manage service deployments with safety guards

## Success Criteria
- [ ] Agent responds within 30 seconds for health checks
- [ ] Log analysis correctly identifies error patterns
- [ ] Deploy operations require human confirmation
- [ ] All actions are logged with trace IDs
- [ ] Cost limits prevent runaway API usage

## Features

### Observability
- Structured logging with session trace IDs
- Every LLM call and tool execution traced
- Logs written to `logs/agent.log`

### Safety
- **Permission gates**: READ is auto-approved, WRITE/EXECUTE require confirmation, DELETE is blocked
- **Dry run mode**: `--dry-run` flag skips all write operations
- **Cost limits**: max 100K input tokens, 50K output tokens, 30 tool calls, 5 minutes

### Reliability
- **Error retry**: exponential backoff on LLM call failures
- **Timeout**: 5-minute session timeout
- **Graceful degradation**: tool failures return error JSON, don't crash the agent

### Deployment
```bash
# Install
pip install openai python-dotenv

# 在 .env 中配置 MIMO_BASE_URL, MIMO_API_KEY, MIMO_MODEL

# Run interactively
python src/agent.py

# Run with a specific task
python src/agent.py --task "Check system health"

# Dry run mode (no write operations)
python src/agent.py --dry-run --task "Analyze logs/app.log"
```

## Architecture

```
[CLI Input]
    |
    v
[DevOpsAgent]
    ├── [TraceLogger] ──> logs/agent.log
    ├── [CostTracker] ──> enforce limits
    ├── [PermissionGate] ──> confirm risky ops
    └── [Agent Loop]
         ├── LLM (MiMo)
         └── Tools
              ├── check_system_health
              ├── read_log_file
              ├── list_services
              └── deploy_service
```

## Configuration

| Env Variable | Default | Description |
|-------------|---------|-------------|
| `MIMO_API_KEY` | (required) | MiMo API key |
| `MIMO_BASE_URL` | https://token-plan-cn.xiaomimimo.com/v1 | API base URL |
| `MIMO_MODEL` | mimo-v2.5-pro | Model to use |
| `AGENT_LOG_FILE` | logs/agent.log | Log file path |

## Extending

To add a new tool:

1. Add tool definition in `create_tools()`
2. Add handler function
3. Set permission level
4. Update `SYSTEM_PROMPT` to describe when to use it

## Limitations
- Windows-only system commands (PowerShell)
- No remote server management (local only)
- Simulated deployments (no actual deploy logic)
- No authentication for sensitive operations
