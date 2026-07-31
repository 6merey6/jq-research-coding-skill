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

两个 MCP 服务器为必需：

| 服务器 | 用途 |
|--------|------|
| **chrome-devtools** | 浏览器操控（notebook 交互） |
| **jq-docs** | 聚宽 API 文档查询（可选，有代理/GitHub 可访问时可用） |

**推荐额外配置（可选）：**
- **firecrawl** — jq-docs 不可用时（如中国大陆无代理）的 fallback，见 `references/fallback-doc-urls.md`

### MCP 配置示例

MCP 服务器有三个 scope 可选，每个服务器可独立配置到不同 scope：

| Scope | 存储位置 | 生效范围 |
|-------|---------|---------|
| `project` | 项目根目录 `.mcp.json` | 仅当前项目；可通过 git 共享给团队 |
| `user` | `~/.claude.json` | 所有项目全局生效；可跨机器同步 |
| `local` | `~/.claude.json` | 所有项目全局生效；标记 local-only，不参与同步 |

**project scope（团队共享，推荐）：**

```json
// 项目根目录 .mcp.json
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

**user scope（全局生效，跨机器同步）：**

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

**local scope（全局生效，仅本机，不同步）：**

```json
// ~/.claude.json（和 user scope 同一文件，标记 local-only）
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

> `user` 和 `local` 都存储在 `~/.claude.json` 中。区别在于 `local` 标记为本地配置不参与同步（适合存放个人密钥等敏感内容），而 `user` 可以跨机器同步。`project` 存储在项目 `.mcp.json` 中，可被 git 追踪共享。配置后需重启会话。

## 计费提醒

本 skill 依赖两个（或三个）MCP 服务器，每次操作都会产生 MCP tool call。**按工具调用次数计费的 coding plan 会比按 token 计费的 plan 消耗更多额度。** 如果你的 plan 按调用次数计费，请注意控制操作粒度，合并可以一次完成的操作。

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

将本仓库内容放入平台的 skills 目录，确保 MCP 服务器已配置，重启会话即可。

## 使用

本 skill 会智能检测当前 Chrome 状态，以下三种场景都能自动处理：

### 准备阶段

**A. 完全不启动 Chrome（最简单）**

第一次使用只需：

1. 启动带调试端口的 Chrome（**仅需做一次**，之后 profile 会保留登录态）：
   - Windows：`chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug-profile"`
   - macOS：`/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable`
2. Chrome 打开后，访问 `https://www.joinquant.com` 并登录聚宽账号
3. 在 AI 助手中调用 skill：
   ```
   /jq-research-coding-skill 帮我新建一个 notebook，写一个均线策略
   ```
   skill 会**自动打开研究环境页面**、**创建 notebook**、**写代码并运行**——全程不需要你手动操作浏览器。

后续使用时 Chrome 已保持运行，只需第 3 步即可。

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

### 工作流程

激活后，skill 会自动执行以下闭环：

1. **查文档** — 用 jq-docs MCP（或 firecrawl/WebFetch 兜底）查询需求涉及的聚宽 API
2. **问测试** — 询问是否先测试 API（可选）
3. **写代码** — 在 notebook 中注入代码、执行、读取结果（完整不截断）
4. **清理** — 测试通过后自动删除测试 cell
5. **异常处理** — 内核断开自动诊断和重启，内存 >80% 主动警告并建议分批+del 释放

## 文件结构

```
SKILL.md                              # 核心规则+流程（主文件）
README.md                             # 中文说明
README.en.md                          # English version
references/
  notebook-ui-patterns.md             # Snapshot UI 模式识别
  fallback-doc-urls.md                # 在线文档 fallback URL
  code-templates.md                   # JS 代码模板
```

## 功能覆盖

- ✅ Chrome 智能启动检测（先查端口再查页面）
- ✅ Notebook 创建/打开/重命名
- ✅ Cell 代码注入、执行、完整读取（不截断）
- ✅ 聚宽 API 文档查询（jq-docs MCP 优先，firecrawl/WebFetch 兜底）
- ✅ 内核断开诊断（3 种弹窗类型识别）
- ✅ 内核重启（手动关闭→重新打开 / 自动恢复+规则7兜底）
- ✅ 内存管理（>80% 主动警告+分批+del 释放）
- ✅ 测试代码自动清理
- ✅ Cell 放置判断（新功能末尾新建 / 修改代码回填原 cell，保证 Run All 不报错）
