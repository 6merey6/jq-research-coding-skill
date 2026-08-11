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

One chrome-devtools MCP is required (**pick one or configure both**; the skill chooses based on browser state):

| Server | Purpose |
|--------|---------|
| **chrome-devtools** (browser mode) | Connect to a dedicated debug Chrome (9222); the skill can auto-open an isolated debug window |
| **chrome-devtools-autoconnect** (autoConnect mode) | Connect to your **currently-open Chrome** (needs manual browser open + `chrome://inspect` enabled + click Allow each time) |

> **Browser selection logic**: the skill first checks whether 9222 is a valid debug endpoint (`/json/version` returns HTTP 200, not just the port being open). If valid → browser mode; otherwise → ask the user to choose (see Usage).

**Optional (recommended):**
- **firecrawl** — fallback to verify JoinQuant docs online when the built-in CLI can't find / data seems stale / runtime errors, see `references/fallback-doc-urls.md`

**JoinQuant API doc lookup needs NO extra MCP**: this skill bundles `jq-docs/query_jq_docs.py` (pure Python stdlib sqlite3, data shipped in `jq_knowledge.db`, fully offline, zero dependencies, zero registration) — replacing the former jq-docs MCP.

### MCP Config Example

Three scopes are available. Each server can be configured independently:

| Scope | Location | Effect |
|-------|---------|--------|
| `project` | Project root `.mcp.json` | This project only; can be shared via git |
| `user` | `~/.claude.json` | All projects; syncs across machines |
| `local` | `~/.claude.json` (per-project under `projects`) | **This project + current user only**; marked local-only, never synced |

**Project scope (team sharing, recommended):**

```json
// Project root .mcp.json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    },
    "chrome-devtools-autoconnect": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
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
    "chrome-devtools-autoconnect": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
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
    "chrome-devtools-autoconnect": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
    }
  }
}
```

> **Three config trade-offs**: browser only → skill auto-opens an isolated debug window (fully isolated, but can't use your already-open browser); autoConnect only → uses your currently-open browser (needs manual open + `chrome://inspect` + click Allow each time); both → works in every scenario (use autoConnect when a browser is open, browser mode to auto-open one when nothing is).
>
> `user` scope is stored at the top level of `~/.claude.json` (all projects, syncs across machines). `local` scope is also stored in `~/.claude.json` but **per-project** (under `projects.<path>`), effective for **this project + this user only**, never synced via git (ideal for personal/credential servers). `project` scope stores in `.mcp.json` tracked by git. Restart your session after configuration.

## Billing Notice

This skill depends on chrome-devtools MCP (may have browser + autoConnect instances, but only one is used per browser operation); **JoinQuant API doc lookup runs a local script, generating no MCP calls.** **Plans billed by tool-call count will consume more credits than token-based plans.** If your plan charges per call, batch operations where possible.

## Installation

### Claude Code

```bash
git clone https://github.com/<your-username>/jq-research-coding-skill.git \
  .claude/skills/jq-research-coding-skill
```

### Other Platforms

Place the repository contents into your platform's skills directory, ensure the chrome-devtools MCP server is configured, and restart the session.

> **JoinQuant API doc lookup works out of the box**: `jq-docs/query_jq_docs.py` + `jq_knowledge.db` ship with the repo — **no MCP/dependency install needed** (just Python; sqlite3 is stdlib), fully offline.

## Usage

This skill intelligently detects your current browser state. **If both browser + autoConnect MCPs are configured**:
- 9222 has a valid debug Chrome (`/json/version` returns 200) → use **browser mode**
- otherwise → ask you to choose: **A) open an isolated debug Chrome via browser mode**; **B) debug in your currently-open browser via autoConnect**

### Preparation

**A. Start from scratch (easiest — no manual Chrome setup)**

No need to start the browser manually. Directly invoke in your AI assistant:

```
/jq-research-coding-skill create a new notebook and write an SMA crossover strategy
```

The skill will automatically open the research page, create the notebook, write code and run it — no manual browser interaction needed.
(The skill first detects / auto-starts Chrome with a remote debugging port; if it prompts for JoinQuant login the first time, log in once — the session persists.)

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

> **Note (B/C "already-started browser"):** With **browser mode** (`--browser-url`), the skill **connects** to an already-running debug Chrome (9222); it does not launch a new browser, so B/C works **only if** that browser is the debug Chrome (9222). With **autoConnect mode**, it directly connects to your currently-open Chrome (requires `chrome://inspect` enabled + click Allow each time). If 9222 has no valid debug endpoint, the skill first asks whether to go browser or autoConnect.

### Automated Workflow

Once activated, the skill executes the following closed loop:

1. **Look up docs** — query JoinQuant APIs via the bundled `jq-docs/query_jq_docs.py` (or firecrawl/WebFetch online fallback to verify the official docs)
2. **Ask about testing** — ask if you want to test the APIs first (optional)
3. **Write code** — inject code into notebook, execute, read results (full text, no truncation)
4. **Clean up** — automatically delete test cells after verification
5. **Handle exceptions** — auto-diagnose kernel disconnection, restart kernel, warn at >80% memory and suggest batch + `del` cleanup

## File Structure

```
SKILL.md                              # Core rules and workflows
README.md                             # Chinese README
README.en.md                          # English README
jq-docs/
  query_jq_docs.py                    # JoinQuant API doc lookup CLI (pure local, zero deps)
  jq_knowledge.db                     # JoinQuant API doc SQLite DB (221 functions + 2479 columns)
  LICENSE                             # MIT (from upstream jiaweizhang1995/jq-docs-mcp)
references/
  notebook-ui-patterns.md             # Snapshot UI pattern reference
  fallback-doc-urls.md                # Online doc fallback URLs
  code-templates.md                   # JS code templates for cell operations
```

## Features

- ✅ Smart Chrome startup detection (check port, then pages)
- ✅ Notebook creation, opening, renaming
- ✅ Cell code injection, execution, and complete output reading (no truncation)
- ✅ JoinQuant API doc lookup (bundled `jq-docs/query_jq_docs.py` first, firecrawl/WebFetch online fallback)
- ✅ Kernel disconnection diagnostics (3 popup types)
- ✅ Kernel restart (manual shutdown → reopen / auto-recovery with fallback)
- ✅ Memory management (>80% proactive warning + batch processing + `del` cleanup)
- ✅ Automatic test cell cleanup
- ✅ Smart cell placement (new code at end / modify in-place, ensures Run All works)
