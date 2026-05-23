# Stage 6: Browser Agent

## Deliverable
A browser agent that navigates web pages, extracts information, and generates summaries.

## Architecture

```
User Query
    |
    v
[Browser Agent]
    |
    ├── navigate(url) ──> page metadata
    ├── extract_text() ──> page content
    ├── extract_links() ──> link list
    ├── click(selector) ──> interaction
    └── screenshot() ──> audit trail
    |
    v
[Research Summary]
```

## Safety Guards

| Guard | Implementation |
|-------|---------------|
| **URL validation** | Only http/https allowed |
| **No form submission** | `click()` refuses to submit `<form>` elements |
| **Text truncation** | Extracted text capped at 5000 chars |
| **Link limit** | Max 50 links per extraction |
| **Timeout** | 30s page load timeout |
| **Audit trail** | Every action logged with `_log()` |
| **Headless mode** | Default headless, no visible browser |

## How to Run
```bash
pip install playwright
playwright install chromium
python browser_agent.py
```

## Limitations
- Uses Google search (may be blocked without proper headers)
- No JavaScript-heavy SPA support (basic domcontentloaded)
- No authentication or login (by design - safety)
- Screenshots are viewport-only, not full-page

## References
- [browser-use](https://github.com/browser-use/browser-use)
- [Playwright Docs](https://playwright.dev/python/)
- [Claude Computer Use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use-tool)
