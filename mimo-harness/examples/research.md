# Research Examples

## Web Search
```
mimo-harness --task "Search the web for the latest news about Xiaomi MiMo model"
```

## Fetch and Analyze
```
mimo-harness --task "Fetch the content from https://example.com and summarize the key points"
```

## Multi-step Research
```
mimo-harness --task "Search for 'AI agent frameworks 2026', fetch the top 3 results, and create a comparison document"
```

## Code Research
```
mimo-harness --task "Search the web for 'Python async best practices' and create a cheatsheet markdown file"
```

## Pipe and Analyze
```
curl -s https://api.example.com/data | mimo-harness -p "Analyze this JSON data and identify trends"
```

## Research with Session Resume
```
# Start research
mimo-harness --name "ml-research" --task "Search for recent papers on transformer architectures"

# Continue later
mimo-harness --resume
# Pick "ml-research" session to continue
```

## Low-Effort Quick Lookup
```
mimo-harness --effort low --bare --task "What is the capital of France?"
```

## Document Analysis
```
mimo-harness --task "Read the 3 PDF reports in the reports/ directory and create a comparison matrix"
```
