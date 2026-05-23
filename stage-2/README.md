# Stage 2: Research Assistant with RAG, Memory, and Citations

## Deliverable
A research assistant agent that searches, filters, summarizes, and outputs with citations.

## Architecture

```
User Query
    |
    v
[Agent Loop] <--> [Memory System]
    |                  |
    v                  v
[Tool Router]    [3-tier Memory]
    |              - Short-term (in-context)
    v              - Session (conversation)
[Tools]            - Long-term (vector store)
    |
    v
[Answer with Citations]
```

## Features

### RAG Pipeline
- **Chunk**: Text split into 500-char overlapping chunks
- **Store**: Chunks saved to simulated vector store with source metadata
- **Retrieve**: Keyword overlap scoring (placeholder for real embeddings)
- **Answer**: LLM generates answers citing retrieved sources

### Memory System (3 tiers)
| Tier | Implementation | Lifetime | Use Case |
|------|---------------|----------|----------|
| Short-term | In-context messages | Single LLM call | Current reasoning |
| Session | `session_history` list | Conversation | Track what was discussed |
| Long-term | Simulated vector store | Persistent | Recall prior research |

### Error Handling
- **Tool failures**: try/except around every tool, error returned to LLM
- **Empty results**: explicit "no results" message so LLM knows to try alternatives
- **Duplicate calls**: `seen_tool_calls` set prevents repeating identical calls
- **Hallucinated citations**: all sources come from actual tool results, not LLM imagination

## Tools
| Tool | Purpose |
|------|---------|
| `web_search` | Search for current information (simulated, connect real API) |
| `read_file` | Read local files, auto-chunks into RAG store |
| `save_to_memory` | Persist findings to long-term memory |
| `recall_memory` | Search long-term memory for prior research |
| `execute_code` | Run Python for data analysis |

## How to Run
```bash
export ANTHROPIC_API_KEY=your-key
pip install anthropic
python research_assistant.py
```

## References
- [LlamaIndex Agents](https://docs.llamaindex.ai/en/stable/use_cases/agents/)
- [LangChain Docs](https://docs.langchain.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [mem0](https://github.com/mem0ai/mem0)
