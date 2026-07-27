# jq-research-coding-skill

> [English version](README.en.md)

在聚宽（JoinQuant）研究环境 notebook 中写代码、运行、调试的 AI 编码助手 skill。通过 Chrome DevTools MCP 操控浏览器 notebook，覆盖内核断开处理、内存溢出管理等完整工作流。

原名 `jq-research-coding-skill`，后缀 `-skill` 表示可在任何支持 Agent Skills 规范的平台上加载。

## 适用平台

本 skill 遵循 [Agent Skills 规范](https://agentskills.io/specification)，可在以下平台使用：

- **Claude Code** — 放入 `.claude/skills/` 目录，通过 `/jq-research-coding-skill` 调用
- **Codex** — 放入 `.codex/skills/` 目录
- **Cursor / VS Code** — 通过插件市场安装
- **其他支持 MCP + Agent Skills 的平台**

## 前置依赖

两个 MCP 服务器为必需：

| 服务器 | 用途 |
|--------|------|
| **chrome-devtools** | 浏览器操控（notebook 交互） |
| **jq-docs** | 聚宽 API 文档查询 |

**推荐额外配置（可选）：**
- **firecrawl** — jq-docs 不可用时（如大陆无代理）的 fallback，见 `references/fallback-doc-urls.md`

### MCP 配置示例（`.mcp.json`）

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

1. 启动带调试端口的 Chrome：
   ```
   chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug-profile"
   ```
2. 在浏览器中打开聚宽 study 页面，登录并打开目标 notebook
3. 在 AI 助手中调用：`/jq-research-coding-skill 帮我写一个策略`

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
