---
name: jq-research-coding-skill
description: Use when writing or debugging code in JoinQuant (聚宽) research notebooks, encountering kernel disconnection, memory overflow, cell execution issues, or needing to query JoinQuant API documentation. Triggers on mentions of 聚宽, JoinQuant, 研究环境, notebook kernel problems, 内存溢出.
---

# 聚宽研究环境 Notebook 编码

## 概述

本 skill 涵盖通过 Chrome DevTools MCP 操作聚宽（JoinQuant）研究 notebook 的完整工作流。强制规范代码编写、执行和调试规则 —— 在回测场景中，数据获取出错可能造成重大财务损失。

## 前置依赖

需要 chrome-devtools MCP（**二选一或同时配置**，skill 会按浏览器状态选择用哪个）：

| 服务器 | 用途 | 配置 |
|--------|------|------|
| **chrome-devtools**（browser 模式） | 连接带调试端口(9222)启动的**独立调试 Chrome** | `npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222` |
| **chrome-devtools-autoconnect**（autoConnect 模式） | 直接连接你**当前打开的 Chrome**（需 Chrome 144+ + 已启用 `chrome://inspect` 远程调试） | `npx -y chrome-devtools-mcp@latest --autoConnect` |

**浏览器选择逻辑**：skill 先检测 9222 是否为**合法调试端点**（`/json/version` 返回 HTTP 200，而非仅端口被占）。合法→用 browser 模式；不合法→询问用户二选一（见"智能启动 Chrome"）。

**聚宽 API 文档查询无需 MCP**：本 skill 自带 `jq-docs/query_jq_docs.py`（纯 Python 标准库 sqlite3，数据随包 `jq_knowledge.db`，完全离线、零依赖、零注册），替代原 jq-docs MCP。

> ⚠️ **计费提醒（必须告知用户，告知后停止等待用户说"继续"）：** 本 skill 依赖 chrome-devtools MCP（若同时配两个，每次浏览器操作只走其中一个，但两个 MCP 进程都会加载）。对于**按工具调用次数计费**的 coding plan，会比按 token 计费的 plan 消耗更多额度。**在 skill 激活后、执行任何操作前，必须先用 AskUserQuestion 告知用户此计费风险，等用户确认"继续"后才能开始工作。**（用户可能需要切换到按 token 计费的 plan。）

### 聚宽 API 文档查询（自带 CLI + 在线兜底）

**主用本 skill 自带脚本**（完全离线、结构化输出）：

```bash
# <skill路径> 是本 skill 所在目录; Windows 示例: python .claude/skills/jq-research-coding-skill/jq-docs/query_jq_docs.py ...
python <skill路径>/jq-docs/query_jq_docs.py lookup  get_price                 # 完整函数文档(签名/参数/返回/示例)
python <skill路径>/jq-docs/query_jq_docs.py search  融资融券                  # 中英文关键词搜索
python <skill路径>/jq-docs/query_jq_docs.py table   FINANCE_INCOME_STATEMENT  # 数据表字段
```

| 优先级 | 方式 | 适用条件 |
|--------|------|---------|
| **1** | 自带 CLI 脚本（`jq-docs/query_jq_docs.py`） | 首选，离线、快、结构化，输出与上游 jq-docs MCP 完全一致 |
| **2** | firecrawl MCP（`firecrawl_scrape`） | **兜底**，抓 `help/data/*` 完整页面，无 GitHub 依赖，已验证可用 |
| **3** | 原生 WebFetch（内置工具） | 原生 Claude 模型可直接用；非原生模型可能被拦截 |

**★★★ 兜底触发规则（必须立即执行，不能将就）：** 出现以下任一情况，**立即**用 firecrawl/WebFetch 重新查询**该 API** 的聚宽官网文档，确认是否已变更，并**以聚宽官网文档为准**：
1. **CLI 脚本查询不到**该 API（`not found` 且相似建议也不匹配）
2. **疑心数据过时**（如涉及近期新增/改名的 API、聚宽公告有变动）
3. **用查询到的 API 写代码后实际运行报错**（参数名/返回结构不对）→ 很可能是 DB 快照落后于官网，必须回官网核对

> 兜底时先看 `https://www.joinquant.com/help/data/<分类>` 对应页面；`help/api/help` 是策略回测文档，不用于研究环境。

**常用 `help/data/*` 文档 URL（在线兜底用）：**

| 数据分类 | URL |
|---------|-----|
| 股票数据（行情/财务/函数） | `https://www.joinquant.com/help/data/stock` |
| 基金数据 | `https://www.joinquant.com/help/data/fund` |
| 指数数据 | `https://www.joinquant.com/help/data/index` |
| 期货数据 | `https://www.joinquant.com/help/data/futures` |

**在线兜底示例：**
- firecrawl: `firecrawl_scrape("https://www.joinquant.com/help/data/stock", formats=["markdown"])` → 获取完整页面后提取 API 信息
- WebFetch: `WebFetch("https://www.joinquant.com/help/data/stock", "提取 get_price 的参数、返回值和示例")` → 原生模型直接分析

> **注意：**
> - `https://www.joinquant.com/help/api/help` 是策略回测文档（含 `order`/`initialize`/`handle_data`），不适用于研究环境，不要引用
> - 只在 `help/data/*` 中查找研究环境可用的 API
> - 非原生 Claude 模型（如 DeepSeek）可能无法使用 WebFetch；建议额外配置 firecrawl MCP
> - 大陆网络环境可能导致任何在线抓取方式都不稳定

### 推荐 `.mcp.json` 配置（project scope）

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    },
    "chrome-devtools-autoconnect": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
    }
  }
}
```

**两种模式的取舍：**
- **browser 模式（`--browser-url`）**：连接"带 `--remote-debugging-port=9222` 启动的独立调试 Chrome"（独立 profile，与日常 Chrome 隔离）。稳定、无弹窗，但需先启动调试 Chrome。
- **autoConnect 模式（`--autoConnect`）**：直接连接你当前打开的 Chrome（共享登录态），**但需 Chrome 144+**，且要**先在浏览器里启用一次** `chrome://inspect/#remote-debugging` 远程调试，每次连接还会**弹权限框点 Allow**。

> 只用一个时：日常就开普通 Chrome → 配 autoConnect 最省事；想完全隔离 → 配 browser 模式。两个都配则由 skill 按浏览器状态选择（见"智能启动 Chrome"）。

### MCP 配置检查（skill 激活时执行）

每次操作 notebook 前，先确认 chrome-devtools 配置情况。**若未配置或不确定，用 AskUserQuestion 询问用户希望配置哪种**，并讲清三者区别：

| 选项 | 能做什么 | 限制 |
|------|---------|------|
| **只配 browser 模式**（`chrome-devtools`） | skill 自动启动一个**独立调试 Chrome 窗口**（独立 profile），聚宽 coding 在该专用窗口执行 | 不能用你已打开的浏览器窗口；每次需 skill 启动调试窗口 |
| **只配 autoConnect 模式**（`chrome-devtools-autoconnect`） | 直接在你**当前打开的 Chrome** 中调试（共享登录态/页面） | ① 需**你手动打开浏览器**（不会自动开）② 需 Chrome 144+ ③ 需在 `chrome://inspect/#remote-debugging` 启用一次远程调试 ④ **每次连接要点 Allow** |
| **两个都配置**（推荐） | 什么场景都能用：你已开浏览器 → 用 autoConnect 直接在你浏览器里调试；你啥都没开 → skill 用 browser 模式自动开一个调试 Chrome 并启用调试 | 多加载一个 MCP 进程（多计费一点） |

**按用户选择给出安装命令（scope 用 AskUserQuestion 让用户选 project/user/local）：**

```bash
# browser 模式（独立调试窗口）
claude mcp add --scope <选择> chrome-devtools -- npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
# autoConnect 模式（连你当前打开的浏览器）
claude mcp add --scope <选择> chrome-devtools-autoconnect -- npx -y chrome-devtools-mcp@latest --autoConnect
```

**firecrawl（可选，推荐配置作为在线兜底）：**
```bash
claude mcp add --scope <选择> firecrawl -- npx -y @anthropic-ai/mcp-server-firecrawl
```

| Scope | 存储位置 | 生效范围 |
|-------|---------|---------|
| `project` | 项目根目录 `.mcp.json` | 仅当前项目；可通过 git 共享给团队 |
| `user` | `~/.claude.json` | 所有项目全局生效；可跨机器同步 |
| `local` | `~/.claude.json`(projects 下按项目存) | **仅当前项目 + 当前用户**；标记 local-only，不参与项目同步 |

> 添加 MCP 服务器后需重启会话。每个服务器可配置到不同 scope。

## Chrome 启动 — 开启远程调试

MCP 服务器必须连接到开启了 DevTools 的 Chrome 实例。

### 智能启动 Chrome（notebook 操作前的必要步骤）

**不要盲目关闭所有 Chrome 窗口。** 先检测 9222 是否为**合法调试端点**，再决定用哪个 MCP：

**(A) 检测 9222 是否合法调试端点（不是只看端口被占）：**
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9222/json/version
```
- 返回 `200` → 9222 有合法调试 Chrome → 用 **browser 模式**（`chrome-devtools`）→ 跳到 (C)
- 返回 `404` 或连接失败 → 9222 无合法调试端点（可能被占用但不是调试 Chrome，如日常 Chrome 异常占位）→ 走 (B) 询问

**(B) 9222 无合法调试端点时，用 AskUserQuestion 让用户二选一：**

**选项1 — 用 browser 模式启动独立调试 Chrome（完全隔离）：**
- 前提：先释放 9222。若 9222 被占用（如当前是你打开的 Chrome），需你先关闭占用它的浏览器窗口。
- skill 随后启动带调试参数的独立 Chrome（独立 profile，见下方启动命令），聚宽 coding 在该专用窗口执行。
- 用 `chrome-devtools`（browser 模式）继续。
- 若你坚持要"别的端口"（不想关 9222 上的浏览器），需在 `.mcp.json` 另配一个指向该端口的 browser MCP（如 `--browser-url=http://127.0.0.1:9223`）。

**选项2 — 用 autoConnect 模式在当前打开的 Chrome 中调试：**
- 前提：你**已手动打开** Chrome（autoConnect 不会自动开浏览器）+ 已启用 `chrome://inspect/#remote-debugging` 远程调试（一次性）+ Chrome 144+。
- 用 `chrome-devtools-autoconnect` 继续；**每次连接会弹权限框，点 Allow**。

启动独立调试 Chrome 的命令（选择对应平台）：

**Windows：**
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug-profile"
```

**macOS：**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable
```

**Linux：**
```bash
/usr/bin/google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable
```

**关键限制：** Chrome 130+ **必须**使用非默认 `--user-data-dir`。即使显式指定默认路径（如 `C:\Users\<name>\AppData\Local\Google\Chrome\User Data`）也会被拒绝。务必使用独立的调试 profile 目录。

> 调试 profile 是持久化的 — 聚宽登录态、cookie、设置都会跨重启保留。首次使用此 profile 时需要登录聚宽，后续会话保持登录状态。

**(C) Chrome 调试端口已开启（或刚启动），检查页面列表：**
- 用 `list_pages` 查看当前浏览器页面
- 如果**已有** notebook 页面和 `https://www.joinquant.com/research` 页面 → 直接复用，跳到准备工作流程
- 如果**缺少**某些页面 → 按准备工作流程补充打开
- **`https://www.joinquant.com/research` 是绝对必需的** — 即使已有 notebook 页面，没有研究页面也必须打开

## 准备工作流程（按步执行）

严格按照以下步骤顺序执行，每步确认后再进入下一步。

### 第零步：计费提醒（必须执行，阻塞式，仅首次）

**在 skill 首次激活时，告知用户计费风险，然后停下来等待用户说"继续"：**

> "⚠️ 此 skill 依赖 chrome-devtools MCP（可能配了 browser + autoConnect 两个实例，但每次浏览器操作只走其中一个），每次操作都会产生 MCP tool call。按工具调用次数计费的 plan 会比按 token 计费的 plan 消耗更多额度。如果使用按次计费的 plan，建议切换到按 token 计费。准备好了请说'继续'。"

- 用户说"继续" → 进入第一步
- 用户说要切换 plan → 等用户切换后重新开始
- **后续调用 skill 时不要再提此事**

### 第一步：检查浏览器页面

使用 `list_pages` 查看当前浏览器状态。**必须** 至少包含 `https://www.joinquant.com/research` 页面。

- 如果研究页面不存在 → 使用 `navigate_page` 或 `new_page` 打开 `https://www.joinquant.com/research`
- 如果弹出登录页面 → 提醒用户登录聚宽平台，用 AskUserQuestion 询问"登录完成了吗？"，确认后再继续

> **⚠️ 规则：** 如果在任何时候发现页面列表中不存在 `https://www.joinquant.com/research` 页面，必须立即重新打开，并提醒用户："必须至少要打开研究环境页面，我才能在聚宽上进行相应的操作。"

### 第二步：选择或创建 Notebook

对研究页面进行 `take_snapshot`。然后使用 AskUserQuestion **同时询问两个问题**：

**问题1：** "你希望我新建一个 notebook 还是打开已有的 notebook？"
- 选项："新建 notebook" / "打开已有 notebook"

**问题2：** "需要我来帮你打开 notebook，还是你自己打开？"
- 选项"我来帮你打开"：根据用户需求在文件列表中选中对应的 `.ipynb` 文件并打开
- 选项"我自己打开"：提示用户："请你自己打开 notebook，打开好了再点击这个选项"，用户点击后继续

**如果选择"新建 notebook"：**
1. 点击"新建"按钮
2. 在下拉菜单中选择"Python 3"
3. 重命名：点击 notebook 标题（"Untitled"），输入新名称，点击"重命名"

**如果选择"打开已有 notebook"：**
1. 由用户或 AI 在文件列表中点击目标 `.ipynb` 文件链接
2. 用 `select_page` 选中新打开的 notebook 页面
3. **用 `evaluate_script` 读取所有 cell 的代码和输出**（见新步骤 2.5），完全了解 notebook 现有内容后再开始下一步

### 第二步半：阅读已有 notebook 的全部内容（仅"打开已有 notebook"时）

如果是打开已有的 notebook，**在开始任何操作前，必须先用 `evaluate_script` 读取所有 cell 的代码和输出**，完全了解 notebook 现有内容后再进入下一步。模板见 `references/code-templates.md` 中的"读取所有 Cell 内容"。

### 第三步：确认准备工作完成

选中 notebook 页面后确认：
- [ ] 存在两个页面：研究页面 + notebook 页面
- [ ] notebook 页面已被选中（使用 `select_page`）
- [ ] 内核指示器显示"Python 3"和"已信任"
- [ ] 内存使用合理（notebook 页面内存 < 80%）

## 编码规则 — 必须遵守

以下规则是**强制性**的。违反任何一条都可能导致回测数据错误，造成重大财务损失。

### 规则1：★★★★★ 充分查阅 API 文档

写代码前，**必须**用本 skill 自带脚本 `jq-docs/query_jq_docs.py` 查阅用户需求涉及的**全部**聚宽 API 方法。需了解：
- 作用（功能说明）
- 全部参数（名称、类型、是否必填）
- 返回值结构（类型、列名、索引）

用 `lookup <函数名>` 查询精确函数名。对于 `query()` 模式和财务数据表，还需用 `table <表名>` 验证字段名。**若 CLI 查不到、疑心数据过时、或按查询结果写的代码实际运行报错，必须立即用 firecrawl/WebFetch 回聚宽官网重新核对，以官网为准**（见"聚宽 API 文档查询"一节兜底触发规则）。查询命令见"jq-docs 查询速查"。

**严禁猜测 API 行为** — 一个错误的假设可能悄无声息地产生错误的回测数据。

### 规则2：★★★ Cell 放置位置 —— 保证一次运行逻辑完整不报错

核心原则：**确保用户直接"Run All"时，代码逻辑完整且不报错。**

**默认做法 — 末尾新建：**
- 添加**全新功能**或**新代码块**时，用 `insert_cell_at_index('code', ncells)` 插到末尾
- 保持顺序：`cell[0] → cell[1] → ... → cell[N]`

**例外 — 回填原 cell：**
- **修改已有代码**（如重写函数）时，应**替换原 cell 的代码**，而非末尾新建
- 在末尾重定义同一函数会导致 Run All 时前面的旧代码先执行，中间依赖 cell 可能用到旧版本

**判断标准：**
- 新增功能 → 末尾新建 | 修改已有代码 → 回填原 cell
- 如果代码依赖前面的 cell 定义，必须放在依赖之后
- 最终目标：Run All 一次性通过，无 NameError/ImportError

```javascript
// 末尾新建
const ncells = J.notebook.get_cells().length;
J.notebook.insert_cell_at_index('code', ncells);

// 回填原 cell
const cells = J.notebook.get_cells();
cells[targetIndex].set_text(newCode);
```

### 规则3：★★★★ 测试代码写法

测试结论**不能**只写"测试通过"，必须写清楚判别标准 + 实际结果 + 是否达标：

```
如果 [判别条件], 算通过; 否则算未通过。
实际结果: [具体输出值]
判定: 通过 / 未通过
```

示例：
```
如果聚宽 profit_ratio_max 是 NULL (True), 算通过; 否则未通过。
实际结果: isna()=[True]
判定: 通过
```

### 规则4：★★★★ 读取 cell 输出/报错必须完整不截断

通过 evaluate_script 读取 notebook cell 的输出或错误时，**禁止**用 `.substring(0, N)` 截断。必须用独立字段返回完整文本：

```javascript
// ✅ 正确：完整返回，不截断
const errs = lastCell.element.find('.output_error');
const err_full = errs.length ? errs.text().trim() : '(none)';

const outs = lastCell.element.find('.output_subarea:not(.output_error)');
let output_full = '';
outs.each(function() {
  output_full += this.innerText || this.textContent || '';
  output_full += '\n';
});
output_full = output_full.trim() || '(none)';

return { err_full, output_full };
```

```javascript
// ❌ 错误：截断丢失关键信息
err.text().trim().substring(0, 400)  // MySQL 错误码在末尾，被截断就丢了
```

### 规则5：★★★★★★ Cell 运行等待 — 用 AskUserQuestion，不在 evaluate_script 中 await

**注入 cell 代码并执行后，不在 evaluate_script 里长时间 await 等待，而是立即返回，然后用 AskUserQuestion 询问用户。**

evaluate_script 的 `protocolTimeout`（约 30 秒）会在长时间 await 时报 `Runtime.callFunctionOn timed out`。但聚宽内核仍在正常运行。

流程：

1. 注入代码到 cell，**先调用 `J.notebook.scroll_to_cell(idx)` 滚动到目标 cell**，再 `J.notebook.execute_cells([idx])` 执行。滚动让用户直接看到正在运行的 cell，无需手动翻找。
   - **★★ 批量运行多个 cell 时（如 `execute_cells([0,1,16,17,18,19,20,21])`），必须 `scroll_to_cell(批次中最后一个cell的idx)`（如 `scroll_to_cell(21)`），而不是第一个**。因为聚宽内核按顺序执行 cell（前一个完成才执行下一个），最后一个 cell 的 `In [*]` 变成数字且有输出时，说明前面所有 cell 都已运行完毕。用户只需盯住最后这个 cell 确认完成即可，无需往下翻找。
2. 用 `AskUserQuestion` 询问用户：
   - **问题：** "cell 是否已运行完毕？"
   - **问题中必须描述正在运行的 cell 内容**，如 "正在运行 `simulate_wealth_process`（策略回测模拟，2020-2026 约 72 个月度调仓）" 或 "正在运行 Cell[14]（`wealth_process = simulate_wealth_process(...)`）"，让用户清楚知道是哪个 cell 在执行、里面有什么关键函数/变量，而不是让用户去数 cell 序号
   - **选项"是，已运行完毕"：** 提示用户：当 cell 的 `In [*]` 中的 `*` 变成数字（如 `In [5]`），且 cell 下方有输出结果（正常输出或报错都算）时，才算完成
   - **选项"否，需要排查"：** 按照规则6和规则7的流程排查
   - **选项"其他问题"：** 根据用户具体描述处理

3. **如果用户选"是"但排查发现 cell 仍未运行完毕（In [*] 还是星号、无输出）：**
   - **再次询问**用户，并具体解释："当 cell 的 In [*] 变成 In [数字] 且有输出时才算完成"
   - 如果用户依旧选"是"且仍未运行完毕 → **不再询问**，按用户选"否"的步骤自行排查

4. **用户选"是"且 cell 确实运行完毕：** 用 evaluate_script 读取输出（完整不截断，见规则4）

### 规则6：★★★★★ 排查内核状态

当用户反馈"cell 未运行"或内核疑似卡住时，按以下诊断流程处理：

**★第0步(优先, 最快最准, 一条 evaluate_script 不依赖 UI)：用 `kernel.is_connected()` 直接判断内核连接**

在 notebook 页 iframe 内 `evaluate_script`(Jupyter 标准 API, 任何 notebook 通用):
```js
const win = document.getElementById('research').contentWindow;
const nb = win.Jupyter.notebook;
return {
  connected: nb.kernel ? nb.kernel.is_connected() : false,     // WebSocket 连接状态
  status:    nb.kernel ? nb.kernel.get_status() : 'no-kernel', // idle/busy/starting/dead/autorestarting
};
```

- `connected=false` 或 `status='dead'/'autorestarting'` → **内核未连接/已断** → 按规则7重启内核(重启会清空全部内存变量，需重新运行该 notebook 的所有定义 cell：基础设施/通用工具/函数定义等，不含触发执行的 cell)
- `connected=true` 且 `status='busy'` → 内核在跑，程序正在执行，**不是卡住** → 回到规则5继续询问用户
- `connected=true` 且 `status='idle'` → 内核正常空闲，说明 cell 已执行完(正常或已报错) → 用规则4完整读取该 cell 输出/报错

> **is_connected() 边界**：只回答内核 WebSocket 是否连着，**不回答内存占用**。内存 >80% 判断仍走规则8(读内存指示器)。

**兜底路径**(仅当 evaluate_script 无法执行 / iframe 不可达 / 需要确认 UI 状态时才走以下步骤)：

**前置判断：** 先通过 `list_pages` 确认是否存在 notebook 页面和 `https://www.joinquant.com/research` 页面。

- **若只存在研究页面** → 直接跳至第(3)步
- **若两者都存在** → 从第(1)步开始

**(1) 检查 notebook 页面是否有"未连接"字样：**
对 notebook 页面进行 `take_snapshot`，查找 `StaticText "未连接"`（通常出现在导航栏 "Python 3" 和 "已信任" 之间）。
- 如果有 → 进入规则7的第(1)步重启内核
- 如果没有 → 进入第(2)步

**(2) 检查 notebook 页面是否有弹窗：**
对 notebook 页面进行 `take_snapshot`，查看是否有弹窗。已发现三种弹窗类型：

| 弹窗 heading | 原因 | 处理 |
|-------------|------|------|
| `"连接失败"` | notebook 服务器连接断开 | 点"确定" → 规则7(1) |
| `"内核正在重启"` | **内存溢出**导致内核崩溃，正在自动重启 | 点"确定" → 等待 → 验证内核 |
| `"内存溢出"` / `"内存不足"` | 内存耗尽警告 | 点"确定" → 规则7(1)，重启后建议分批获取 |

- `"连接失败"` / `"内存溢出"` / `"内存不足"` → 直接进入规则7(1)手动重启
- `"内核正在重启"` → 点击"确定"关闭弹窗，等待 5-8 秒后重新 `take_snapshot` 检查：
  - 若显示 "Python 3 已信任" 且无"未连接" → **已自动恢复**，继续
  - 若仍有"未连接"、或再次弹出"连接失败" → **自动恢复失败，规则7(1)兜底**
- 没有弹窗 → 进入第(3)步

**(3) 检查研究页面文件后的"运行中"字样：**
- 切换到 `https://www.joinquant.com/research` 页面，进行 `take_snapshot`
- 查看文件后面是否有"运行中"字样
- **如果有"运行中"：**
  - 说明程序还在正常运行，没有内存溢出
  - 将 notebook 文件网页关掉（关闭网页不会中断内核运行）
  - 重新点击该文件打开（防止出现多个该文件的页面）
  - 再次向用户发 AskUserQuestion 询问是否运行完毕，这次的"否"选项需要提示："你点击了'否'之后，不会再帮你排查内核的运行状态，将直接重启内核。"
  - 如果用户第二次点击"否" → 进入规则7的第(1)步重启内核
- **如果没有"运行中"：**
  - 进入规则7的第(1)步重启内核

### 规则7：★★★★★★ 重启内核规范

当需要重启内核时（从规则6触发或用户直接要求），按以下流程操作：

> **★重启前确认(防误杀运行中程序)**：先按规则6第0步用 `kernel.is_connected()`/`get_status()` 确认确实需要重启。
> - `connected=true` 且 `status='busy'` → 程序正在运行，**不要重启**(会丢失运行中的取数/执行)，回到规则5继续询问。
> - `connected=false` 或 `status='dead'/'autorestarting'` → 内核确实断了，执行下面重启步骤。

**(1) 清洁关闭并重启：**
在 `https://www.joinquant.com/research` 页面中：
- **如果文件后面有"运行中"字样：** 选中文件前面的小框，点击"关闭"彻底关闭内核。将 notebook 文件页面关掉（如果有的话），重新点击该文件开启内核。
- **如果没有"运行中"字样：** 将 notebook 文件页面关掉（如果有的话），重新点击该文件开启内核。

> **注意：** `close_page` 后页面的 snapshot uid 会变化，重新点击文件打开 notebook 后需重新 `take_snapshot` 再操作。已验证此流程可成功恢复内核。

**(2) 备选方案 — 点击"重启内核"：**
如果第(1)步无效，在 notebook 页面点击"重启内核"按钮（环形箭头图标）。

**(3) 最后手段 — 点击"重启研究环境"：**
如果以上都无效，在研究页面点击"重启研究环境"按钮，重启整个研究环境。

### 规则8：★★★★ 内存管理 — notebook 页面内存 >80% 时主动提醒

**聚宽研究环境给每个用户的内存有限。** 免费用户仅 1G 内存，付费用户可通过购买获得更大内存。在获取大量数据和进行回测时容易出现内存溢出。

**触发条件：** 在 notebook 页面 snapshot 中，如果内存使用指示器（如 `内存使用 850M/1.0G` 即 85%）显示**超过 80%**，必须主动用 AskUserQuestion 询问用户是否需要进行内存管理。

**询问模板：**
> "notebook 内存使用已超过 80%（[当前值]），建议进行内存管理。是否需要我提供建议？"

**管理策略（如果用户需要）：**

1. **分批获取数据：** 将大规模数据获取按时间切分（如按月/周），每批获取完立即处理并 `del` 释放：
   ```python
   # 示例：按月份批获取2016-2026年数据
   for year in range(2016, 2027):
       for month in range(1, 13):
           df_batch = get_price(stocks, start_date=f'{year}-{month:02d}-01', 
                                end_date=f'{year}-{month:02d}-28', ...)
           # 处理这批数据...
           del df_batch  # 释放内存
   ```

2. **回测场景：** 用完一个周期的数据后，用 `del` 删除该周期的变量，再获取下一周期数据。

3. **通用原则：** 识别占用大量内存的 DataFrame/变量，用完立即 `del`；避免在内存中同时保留不需要的历史数据。

**注意：** 具体策略要根据用户的实际场景调整，核心思路是**分批 + del 释放**。

### 阶段1：查阅 API 文档（写代码前必须完成）

对于用户需求涉及的每个聚宽 API 函数，先运行本 skill 自带的查询脚本（纯本地，离线）：

```bash
# <skill路径> 是本 skill 所在目录
python <skill路径>/jq-docs/query_jq_docs.py lookup get_price                     # 函数完整文档(签名/参数/返回/示例)
python <skill路径>/jq-docs/query_jq_docs.py search 融资融券                      # 关键词搜索
python <skill路径>/jq-docs/query_jq_docs.py table FINANCE_INCOME_STATEMENT       # 表字段
python <skill路径>/jq-docs/query_jq_docs.py sections                             # 列出分类
python <skill路径>/jq-docs/query_jq_docs.py section "策略API > 策略API介绍"       # 分类内函数
python <skill路径>/jq-docs/query_jq_docs.py functions                            # 全部函数
python <skill路径>/jq-docs/query_jq_docs.py search-in-section 分红 "股票数据 > 获取报告期财务数据"  # 分类内搜索
```

**★CLI 查询不到 / 疑心过时 / 实际运行报错时，立即用在线兜底核对聚宽官网：**
1. 先查 `WebFetch("https://www.joinquant.com/data")` 找到对应数据分类
2. 再查 `WebFetch("https://www.joinquant.com/help/data/<分类>")` 获取 API 函数、参数和返回值
3. WebFetch 不完整时 → 用 `firecrawl_scrape` 获取页面完整内容
4. **以聚宽官网文档为准**（DB 是快照，可能落后于官网）

> **不要用** `https://www.joinquant.com/help/api/help`（策略回测文档，不是研究环境 API）

常用函数速查：

| 类别 | 常用函数 |
|------|---------|
| 行情数据 | `get_price`, `history`, `attribute_history`, `get_bars`（多股票 `get_price` 需加 `panel=False`，Panel 已弃用） |
| 基本面 | `get_fundamentals`, `get_fundamentals_continuously`, `query` |
| 财务表 | `FINANCE_BALANCE_SHEET`, `FINANCE_INCOME_STATEMENT`, `FINANCE_CASHFLOW_STATEMENT` |
| 股票信息 | `get_security_info`, `get_all_securities`, `get_index_stocks` |
| 交易日历 | `get_trade_days`, `get_trade_day` |

### 阶段2：询问用户是否测试 API

查阅完所有需要的 API 后，用 AskUserQuestion 询问用户：

> "查询完 API 文档后，是否需要在 notebook 中先测试一下这些 API 的行为和返回值？"

- **"是，先测试API"：** 对每个 API 函数写测试代码并运行。如果符合预期 → **立即删除测试 cell**，继续写正式代码。如果不符合预期 → 重新查文档、重新测试。
- **"否，直接写代码"：** 跳过测试，直接进入阶段3。

> **⚠️ 清理规则：** 任何测试 cell、调试 cell、验证 cell（如 `print("kernel OK")`），在确认其不再需要后，**必须立即用 `J.notebook.delete_cells([idx])` 删除**，不得遗留在 notebook 中。这保持 notebook 干净，避免后续代码执行时混入无关输出。

### 阶段3：写代码并运行

1. 在 notebook 最末尾新建 cell 写代码（规则2）
2. 执行：注入代码 → `J.notebook.execute_cells([idx])` → 立即返回（批量运行多个 cell 时，先 `scroll_to_cell(最后一个cell的idx)` 滚动到最后，见规则5）
3. 用 AskUserQuestion 询问用户 cell 是否运行完毕（规则5）
4. 完整读取输出（规则4）
5. 按测试格式报告结果（规则3，如果是测试代码）；如果是正式代码，展示输出
6. 如果有错误 → 查看错误信息 → 重新查询相关 API 文档 → 修复 → 重新运行

### Cell 执行/读取/删除/内存检查代码模板

> 完整 JS 模板见 [references/code-templates.md](references/code-templates.md)。包含：注入执行 cell、完整读取输出、删除 cell、批量读取所有 cell、检查内存使用。

核心要点：
- 注入执行：`insert_cell_at_index('code', ncells)` 或回填 `cells[idx].set_text()` → `execute_cells([idx])`（批量运行多个 cell 时滚动到最后：`scroll_to_cell(lastIdx)`）
- 读取输出：`err_full: err.text()` 完整不截断 + `output_full: innerText` 完整
- 删除 cell：`J.notebook.delete_cells([idx])`
- 内存读取：snapshot 中找 `"内存使用 XXXM/X.XG"` button

## chrome-devtools 工具速查

| 任务 | 工具 | 备注 |
|------|------|------|
| 列出浏览器页面 | `list_pages` | 确认研究页面 + notebook 页面存在 |
| 选中页面 | `select_page` | `bringToFront: true` |
| 打开 URL | `navigate_page` 或 `new_page` | `type: "url"` |
| 查看页面内容 | `take_snapshot` | 显示所有 UI 元素及 uid |
| 点击按钮 | `click` | 使用 snapshot 中的 uid |
| 填写文本 | `fill` | 使用 snapshot 中的 uid |
| 在页面中执行 JS | `evaluate_script` | 用于调用 Jupyter API |
| 截图 | `take_screenshot` | 可视化验证 |

## jq-docs 查询速查（自带 CLI）

> 脚本路径: `<skill路径>/jq-docs/query_jq_docs.py`。纯本地离线，输出与上游 jq-docs MCP 完全一致。

| 任务 | 命令示例 |
|------|------|
| 查看所有可用函数 | `python <skill路径>/jq-docs/query_jq_docs.py functions` |
| 函数详细文档 | `python <skill路径>/jq-docs/query_jq_docs.py lookup get_price` |
| 数据表字段定义 | `python <skill路径>/jq-docs/query_jq_docs.py table FINANCE_INCOME_STATEMENT` |
| 关键词搜索 | `python <skill路径>/jq-docs/query_jq_docs.py search 分红` |
| 列出所有分类 | `python <skill路径>/jq-docs/query_jq_docs.py sections` |
| 某分类下函数 | `python <skill路径>/jq-docs/query_jq_docs.py section "策略API > 策略API介绍"` |
| 分类内搜索 | `python <skill路径>/jq-docs/query_jq_docs.py search-in-section 分红 "股票数据 > 获取报告期财务数据"` |

## 常见错误

| 错误做法 | 为什么错 | 正确做法 |
|---------|---------|---------|
| 用 `.substring(0, N)` 截断错误信息 | 截断丢失末尾的 MySQL 错误码 | 返回 `err_full: err.text()` — 完整文本（规则4） |
| 在 evaluate_script 中 `await` | 超时约 30 秒会导致调用失败 | 立即返回，用 AskUserQuestion（规则5） |
| 使用 `J.notebook.execute_cell(cell)` | 执行不可靠 | 使用 `J.notebook.execute_cells([idx])` |
| 修改代码在末尾新建 cell | Run All 时旧定义先执行，依赖 cell 用错版本 | 修改已有代码回填原 cell，新增功能末尾新建（规则2） |
| 写"测试通过"无详情 | 没有证据和审计轨迹 | 完整格式：判别条件 + 实际结果 + 判定（规则3） |
| 猜测 API 参数 | 回测数据错误 = 财务损失 | 始终先查完整文档（规则1） |
| Chrome 用默认 user data dir | Chrome 130+ 拒绝调试端口 | 使用 `--user-data-dir=<非默认目录>` |
| notebook 页面关闭后不复原 | 上下文丢失，内核仍在运行 | 从研究页面重新打开 |
| 内存>80%不及时管理 | 内存溢出导致内核中断，数据丢失 | 主动提醒用户分批+del释放（规则8） |
| 盲目关闭所有 Chrome 窗口 | 打断用户现有工作 | 先检查端口和页面，缺什么补什么 |

## 红色警报 — 立即停止自查

- [ ] 还没查阅所有需要的 API 函数 → **停，先跑 jq-docs 查询脚本（或在线兜底核对官网）**
- [ ] 在使用 `.substring()` 限制输出长度 → **停，返回完整文本**
- [ ] evaluate_script 中有 `await` 等待 → **停，改用 AskUserQuestion**
- [ ] 新建 cell 不在 notebook 末尾 → **停，用 `insert_cell_at_index('code', ncells)`**
- [ ] 研究页面不在 `list_pages` 中 → **停，立即重新打开**
- [ ] 准备写"测试通过" → **停，用完整测试格式**
- [ ] Chrome 未带 `--user-data-dir` 启动 → **停，重新正确启动 Chrome**
- [ ] notebook 页面内存 > 80% 未提醒用户 → **停，询问用户是否需要内存管理**

## 参考文件

本 skill 包含多个 reference 文件，在需要精确匹配 UI 模式或在线兜底查 API 文档时查阅：

| 文件 | 用途 | 何时查阅 |
|------|------|---------|
| [references/notebook-ui-patterns.md](references/notebook-ui-patterns.md) | Snapshot UI 模式：内存指示器、内核状态、3种弹窗 heading、uid 生命周期、工具栏按钮 | 需要识别 snapshot 中的具体元素时 |
| [references/fallback-doc-urls.md](references/fallback-doc-urls.md) | CLI 脚本查不到/疑心过时时的替代文档 URL、已验证的 `help/data/*` 页面、firecrawl/WebFetch 用法 | 需要在线兜底核对聚宽官网 API 文档时 |
| [references/code-templates.md](references/code-templates.md) | 注入执行 cell、完整读取输出、删除 cell、批量读取、内存检查的 JS 模板 | 需要在 notebook 中执行 JS 操作时复制模板 |
| [jq-docs/query_jq_docs.py](jq-docs/query_jq_docs.py) | 聚宽 API 文档查询 CLI（纯本地离线，替代 jq-docs MCP） | 写聚宽代码前查函数签名/参数/表字段 |
