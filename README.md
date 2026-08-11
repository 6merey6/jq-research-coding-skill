# jq-research-coding-skill

> [English version](README.en.md)

在聚宽（JoinQuant）研究环境 notebook 中写代码、运行、调试的 AI 编码助手 skill。通过 Chrome DevTools MCP 操控浏览器 notebook，覆盖内核断开处理、内存溢出管理等完整工作流。

原名 `jq-research-coding-skill`，后缀 `-skill` 表示可在任何支持 Agent Skills 规范的平台上加载。

## 适用平台

本 skill 遵循 [Agent Skills 规范](https://agentskills.io/specification)，可在以下平台使用：

- **Claude Code** — 放入 `.claude/skills/` 目录，通过 `/jq-research-coding-skill` 调用
- **Codex** — 放入 `.codex/skills/` 目录
- **其他支持 MCP + Agent Skills 的平台**

## 前置依赖

需要 chrome-devtools MCP（**二选一或都配**，skill 会按浏览器状态选择用哪个）：

| 服务器 | 用途 |
|--------|------|
| **chrome-devtools**（browser 模式） | 连接独立调试 Chrome（9222）；skill 可自动开一个独立调试窗口 |
| **chrome-devtools-autoconnect**（autoConnect 模式） | 直接连你**当前打开的 Chrome**（需手动开浏览器 + `chrome://inspect` 启用 + 每次点 Allow） |

> **浏览器选择逻辑**：skill 先检测 9222 是否为合法调试端点（`/json/version` 返回 HTTP 200，而非仅端口被占）。合法→用 browser 模式；不合法→询问用户二选一（见"使用"）。

**聚宽 API 文档查询无需额外 MCP**：本 skill 自带 `jq-docs/query_jq_docs.py`（纯 Python 标准库 sqlite3，数据随包 `jq_knowledge.db`，完全离线、零依赖、零注册），替代原 jq-docs MCP。

**推荐额外配置（可选）：**
- **firecrawl** — 自带 CLI 查不到/疑心数据过时/实际运行报错时，在线核对聚宽官网的 fallback，见 `references/fallback-doc-urls.md`

### MCP 配置示例

MCP 服务器有三个 scope 可选，每个服务器可独立配置到不同 scope：

| Scope | 存储位置 | 生效范围 |
|-------|---------|---------|
| `project` | 项目根目录 `.mcp.json` | 仅当前项目；可通过 git 共享给团队 |
| `user` | `~/.claude.json` | 所有项目全局生效；可跨机器同步 |
| `local` | `~/.claude.json`(projects 下按项目存) | **仅当前项目 + 当前用户**；标记 local-only，不参与项目同步 |

**project scope（团队共享，推荐）：**

```json
// 项目根目录 .mcp.json
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

**user scope（全局生效，跨机器同步）：**

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

**local scope（全局生效，仅本机，不同步）：**

```json
// ~/.claude.json（和 user scope 同一文件，标记 local-only）
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

> **三种配置方式取舍**：只配 browser → skill 自动开独立调试窗口（完全隔离，但不能用你已开的浏览器）；只配 autoConnect → 用你当前打开的浏览器（需手动开 + `chrome://inspect` 启用 + 每次点 Allow）；两个都配 → 任何场景都能用（你已开浏览器就用 autoConnect，没开就用 browser 自动开）。
>
> `user` 存储在 `~/.claude.json` 顶层（所有项目生效，可跨机器同步）；`local` 也存储在 `~/.claude.json` 但**按项目隔离**（`projects.<路径>`，仅当前项目 + 当前用户，不参与项目 git 同步，适合个人/密钥类配置）；`project` 存储在项目 `.mcp.json` 中，可被 git 追踪共享。配置后需重启会话。

## 计费提醒

本 skill 依赖 chrome-devtools MCP（可能配了 browser + autoConnect 两个实例，但每次浏览器操作只走其中一个）；**聚宽 API 文档查询走本地脚本，不产生 MCP 调用**。**按工具调用次数计费的 coding plan 会比按 token 计费的 plan 消耗更多额度。** 如果你的 plan 按调用次数计费，请注意控制操作粒度，合并可以一次完成的操作。

## 安装

### Claude Code

```bash
# 放入项目 skills 目录
git clone https://github.com/<your-username>/jq-research-coding-skill.git \
  .claude/skills/jq-research-coding-skill

# 或全局安装
git clone https://github.com/<your-username>/jq-research-coding-skill.git \
  ~/.claude/skills/jq-research-coding-skill
```

### 其他平台

将本仓库内容放入平台的 skills 目录，确保 chrome-devtools MCP 服务器已配置，重启会话即可。

> **聚宽 API 文档查询开箱即用**：`jq-docs/query_jq_docs.py` + `jq_knowledge.db` 已随仓库分发，**无需安装任何 MCP/依赖**（只需本机有 Python，sqlite3 是标准库），完全离线可用。

## 使用

本 skill 会智能检测当前浏览器状态。**若同时配置了 browser + autoConnect 两个 MCP**：
- 9222 有合法调试 Chrome（`/json/version` 返回 200）→ 用 **browser 模式**继续
- 否则 → 询问你二选一：**A) 用 browser 模式开一个独立调试 Chrome**（完全隔离）；**B) 用 autoConnect 在你当前打开的浏览器里调试**

以下三种场景都能自动处理：

### 准备阶段

**A. 完全不启动 Chrome（最简单）**

不需要手动启动浏览器。直接在 AI 助手中调用：

```
/jq-research-coding-skill 帮我新建一个 notebook，写一个均线策略
```

skill 会自动打开研究环境页面、创建 notebook、写代码并运行——全程不需要你手动操作浏览器。
（skill 会先检测/自动启动带调试端口的 Chrome；首次若提示聚宽登录，按提示登录一次即可，后续登录态保留。）

**B. 只想打开研究环境页面**

如果 Chrome 已在运行但没有任何聚宽页面：

```
/jq-research-coding-skill 打开研究环境，打开我的 xxx.ipynb
```

skill 会自动检测页面状态，缺失的研究环境页面会自动打开。如果检测到登录页，会等你登录后再继续。

**C. 已经打开了研究环境和 notebook 页面**

如果已经在浏览器中打开了 `https://www.joinquant.com/research` 和具体的 notebook 页面：

```
/jq-research-coding-skill 帮我修改 cal_portfolio_weight_series 函数
```

skill 会直接选中 notebook 页面开始工作，不重复打开任何页面。

> **注意（B/C 的"已启动浏览器"）：** 若用 **browser 模式**（`--browser-url`），它**连接**已运行的调试 Chrome（9222），不会新建浏览器；B/C 能"在你已启动的浏览器继续"的**前提**是那个浏览器是调试 Chrome（9222）。若用 **autoConnect 模式**，则直接连你当前打开的 Chrome（前提：已启用 `chrome://inspect` 远程调试 + 每次点 Allow）。若 9222 无合法调试端点，skill 会先问你走 browser 还是 autoConnect。

### 工作流程

激活后，skill 会自动执行以下闭环：

1. **查文档** — 用本 skill 自带 `jq-docs/query_jq_docs.py`（或 firecrawl/WebFetch 在线兜底核对官网）查询需求涉及的聚宽 API
2. **问测试** — 询问是否先测试 API（可选）
3. **写代码** — 在 notebook 中注入代码、执行、读取结果（完整不截断）
4. **清理** — 测试通过后自动删除测试 cell
5. **异常处理** — 内核断开自动诊断和重启，内存 >80% 主动警告并建议分批+del 释放

## 文件结构

```
SKILL.md                              # 核心规则+流程（主文件）
README.md                             # 中文说明
README.en.md                          # English version
jq-docs/
  query_jq_docs.py                    # 聚宽 API 文档查询 CLI（纯本地离线，零依赖）
  jq_knowledge.db                     # 聚宽 API 文档 SQLite 数据库（221函数+2479字段）
  LICENSE                             # MIT（上游 jiaweizhang1995/jq-docs-mcp）
references/
  notebook-ui-patterns.md             # Snapshot UI 模式识别
  fallback-doc-urls.md                # 在线文档 fallback URL
  code-templates.md                   # JS 代码模板
```

## 功能覆盖

- ✅ Chrome 智能启动检测（先查端口再查页面）
- ✅ Notebook 创建/打开/重命名
- ✅ Cell 代码注入、执行、完整读取（不截断）
- ✅ 聚宽 API 文档查询（自带 `jq-docs/query_jq_docs.py` 优先，firecrawl/WebFetch 在线兜底）
- ✅ 内核断开诊断（3 种弹窗类型识别）
- ✅ 内核重启（手动关闭→重新打开 / 自动恢复+规则7兜底）
- ✅ 内存管理（>80% 主动警告+分批+del 释放）
- ✅ 测试代码自动清理
- ✅ Cell 放置判断（新功能末尾新建 / 修改代码回填原 cell，保证 Run All 不报错）
