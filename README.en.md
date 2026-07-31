# jq-research-coding-skill

> [中文版](README.md)

An AI coding agent skill for writing, running, and debugging code in JoinQuant (聚宽) research notebooks via Chrome DevTools MCP. Covers kernel disconnection handling, memory overflow management, and the complete notebook workflow.

The `-skill` suffix indicates it can be loaded on any platform supporting the Agent Skills specification.

## Supported Platforms

This skill follows the [Agent Skills spec](https://agentskills.io/specification) and works on:

- **Claude Code** — place in `.claude/skills/`, invoke via `/jq-research-coding-skill`
- **Codex** — place in `.codex/skills/`
- **Any MCP + Agent Skills compatible platform**

## Prerequisites

One MCP server required:

| Server | Purpose |
|--------|---------|
| **chrome-devtools** | Browser control (notebook interaction) |

**Optional (recommended):**
- **jq-docs** — JoinQuant API documentation lookup (requires GitHub access)
- **firecrawl** — fallback when jq-docs is unavailable (e.g., Mainland China without a proxy), see `references/fallback-doc-urls.md`

### MCP Config Example

Three scopes are available. Each server can be configured independently:

| Scope | Location | Effect |
|-------|---------|--------|
| `project` | Project root `.mcp.json` | This project only; can be shared via git |
| `user` | `~/.claude.json` | All projects; syncs across machines |
| `local` | `~/.claude.json` | All projects; marked local-only, never synced |

**Project scope (team sharing, recommended):**

```json
// Project root .mcp.json
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

**User scope (all projects, synced):**

```json
// ~/.claude.json
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

**Local scope (all projects, this machine only, not synced):**

```json
// ~/.claude.json (same file as user scope, marked local-only)
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

> `user` and `local` are both stored in `~/.claude.json`. `local` entries are marked local-only (not synced — ideal for personal API keys), while `user` entries sync across machines. `project` scope stores in `.mcp.json` tracked by git. Restart your session after configuration.

## Billing Notice

This skill depends on two (or three) MCP servers — every operation generates MCP tool calls. **Plans billed by tool-call count will consume more credits than token-based plans.** If your plan charges per call, batch operations where possible.

## Installation

### Claude Code

```bash
git clone https://github.com/<your-username>/jq-research-coding-skill.git \
  .claude/skills/jq-research-coding-skill
```

### Other Platforms

Place the repository contents into your platform's skills directory, ensure MCP servers are configured, and restart the session.

## Usage

This skill intelligently detects your current Chrome state. All three scenarios below are handled automatically:

### Preparation

**A. Start from scratch (easiest for first-time users)**

First-time setup only:

1. Start Chrome with remote debugging (**one-time step** — your login session persists in the debug profile):
   - Windows: `chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug-profile"`
   - macOS: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable`
2. Visit `https://www.joinquant.com` in Chrome and log in to your JoinQuant account
3. Invoke the skill in your AI assistant:
   ```
   /jq-research-coding-skill create a new notebook and write an SMA crossover strategy
   ```
   The skill will **automatically open the research page**, **create the notebook**, **write code and run it** — no manual browser interaction needed.

For subsequent sessions, Chrome stays running — just skip to step 3.

**B. Want to open just the research page**

If Chrome is running but no JoinQuant pages are open:

```
/jq-research-coding-skill open the research environment and open my xxx.ipynb
```

The skill detects the missing research page and opens it automatically. If a login page appears, it will wait for you to log in before continuing.

**C. Research + notebook pages already open**

If you already have `https://www.joinquant.com/research` and a notebook page open in Chrome:

```
/jq-research-coding-skill help me modify the cal_portfolio_weight_series function
```

The skill will directly select the notebook page and start working — no duplicate pages opened.

### Automated Workflow

Once activated, the skill executes the following closed loop:

1. **Look up docs** — query JoinQuant APIs via jq-docs MCP (or firecrawl/WebFetch fallback)
2. **Ask about testing** — ask if you want to test the APIs first (optional)
3. **Write code** — inject code into notebook, execute, read results (full text, no truncation)
4. **Clean up** — automatically delete test cells after verification
5. **Handle exceptions** — auto-diagnose kernel disconnection, restart kernel, warn at >80% memory and suggest batch + `del` cleanup

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
