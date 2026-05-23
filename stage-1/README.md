# Stage 1: Minimal Agent Loop

## Deliverable
A 115-line Python agent that can select tools, execute them, and return final answers.

## What It Does
1. Sends user message + tool definitions to Claude API
2. Claude decides which tool(s) to call (or returns a final answer)
3. If tool_use: executes the tool, feeds results back, loops
4. If end_turn: returns the final text answer
5. Has max_steps (10) and timeout (60s) safety guards

## Tools Available
- `calculator` -- evaluates math expressions
- `search` -- placeholder for search API
- `read_file` -- reads local files

## How to Run
```bash
export ANTHROPIC_API_KEY=your-key-here
pip install anthropic
python minimal_agent.py
```

## Key Concepts Learned
- **Structured JSON output**: Claude's tool_use response is already structured JSON
- **Tool call parsing**: The API returns `tool_use` content blocks with `name`, `input`, and `id`
- **Agent loop**: observe (user input) -> think (LLM decides) -> act (tool execution) -> observe (tool result)
- **Safety**: max_steps prevents infinite loops, timeout prevents hangs, error handling catches tool failures

## References
- [Claude Tool Use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
