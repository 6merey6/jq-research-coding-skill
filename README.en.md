# jq-research-coding-skill

> [中文版](README.md)

An AI coding agent skill for writing, running, and debugging code in JoinQuant (聚宽) research notebooks via Chrome DevTools MCP. Covers kernel disconnection handling, memory overflow management, and the complete notebook workflow.

The `-skill` suffix indicates it can be loaded on any platform supporting the Agent Skills specification.

## Supported Platforms

This skill follows the [Agent Skills spec](https://agentskills.io/specification) and works on:

- **Claude Code** — place in `.claude/skills/`, invoke via `/jq-research-coding-skill`
- **Codex** — place in `.codex/skills/`
- **Cursor / VS Code** — install via plugin marketplace
- **Any MCP + Agent Skills compatible platform**

## Prerequisites

Two MCP servers required:

| Server | Purpose |
|--------|---------|
| **chrome-devtools** | Browser control (notebook interaction) |
| **jq-docs** | JoinQuant API documentation lookup |

**Optional (recommended):**
- **firecrawl** — fallback when jq-docs is unavailable (e.g., mainland China without proxy), see `references/fallback-doc-urls.md`

### MCP Config Example (`.mcp.json`)

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    },
    "jq-docs": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/jiaweizhang1995/jq-docs-mcp", "jq-docs-mcp"]
    }
  }
}
```

## Installation

### Claude Code

```bash
git clone https://github.com/<your-username>/jq-research-coding-skill.git \
  .claude/skills/jq-research-coding-skill
```

### Other Platforms

Place the repository contents into your platform's skills directory, ensure MCP servers are configured, and restart the session.

## Usage

1. Start Chrome with remote debugging:
   - Windows: `chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug-profile"`
   - macOS: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable`
2. Open your JoinQuant notebook in the browser
3. Invoke in your AI assistant: `/jq-research-coding-skill help me write a strategy`

## File Structure

```
SKILL.md                              # Core rules and workflows
README.md                             # Chinese README
README.en.md                          # English README
references/
  notebook-ui-patterns.md             # Snapshot UI pattern reference
  fallback-doc-urls.md                # Online doc fallback URLs
  code-templates.md                   # JS code templates for cell operations
```

## Features

- ✅ Smart Chrome startup detection (check port, then pages)
- ✅ Notebook creation, opening, renaming
- ✅ Cell code injection, execution, and complete output reading (no truncation)
- ✅ JoinQuant API doc lookup (jq-docs MCP first, firecrawl/WebFetch fallback)
- ✅ Kernel disconnection diagnostics (3 popup types)
- ✅ Kernel restart (manual shutdown → reopen / auto-recovery with fallback)
- ✅ Memory management (>80% proactive warning + batch processing + `del` cleanup)
- ✅ Automatic test cell cleanup
- ✅ Smart cell placement (new code at end / modify in-place, ensures Run All works)
