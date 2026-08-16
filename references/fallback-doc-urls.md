# Fallback 文档 URL — jq-docs MCP 不可用时使用

jq-docs MCP 需要从 GitHub 拉取，在大陆无代理时不可用。本文档记录替代方案。

## 优先级

1. jq-docs MCP (`lookup_function` / `search_docs`)
2. **本地 websearch MCP** (open-websearch, `fetchWebContent`/`search`, 本地运行走本地出口, 2026-08实测可访问聚宽官网; ⚠️firecrawl 云端海外被聚宽"非大陆IP"拒)
3. 原生 WebFetch（仅原生 Claude 模型可用，DeepSeek 等可能被拦截）

## 已验证的文档 URL

### 研究环境数据文档 (`help/data/*`)

| 数据分类 | URL | 已验证 |
|---------|-----|--------|
| 股票数据（行情/财务/函数） | `https://www.joinquant.com/help/data/stock` | ✅ |
| 基金数据 | `https://www.joinquant.com/help/data/fund` | 推测存在 |
| 指数数据 | `https://www.joinquant.com/help/data/index` | 推测存在 |
| 金融期货数据 | `https://www.joinquant.com/help/data/futures` | ✅ |

### 数据字典（导航用）

- `https://www.joinquant.com/data` — 数据分类总览，包含各种数据类型的导航链接

### 不使用的 URL

- `https://www.joinquant.com/help/api/help` — 这是策略回测文档（含 `order`/`initialize`/`handle_data`），**不适用于研究环境**

---

## 本地 websearch (open-websearch) 使用方式

### 配置（可选, 推荐作为聚宽官网兜底; 若 WebFetch 正常可不配置）

```bash
# Claude Code 用 stdio(npx 通用方式; 生成全局 npm 缓存可清理, 非项目内)
claude mcp add --scope <project|user|local> web-search -- npx -y open-websearch@latest
# env 可选(走本地代理访问受限站点; 默认 duckduckgo)
# USE_PROXY=true PROXY_URL=http://127.0.0.1:7890 MODE=stdio DEFAULT_SEARCH_ENGINE=duckduckgo
```

### 使用方法

```javascript
// 抓取完整页面(本地出口, 2026-08实测可访问聚宽官网 help/data/stock)
fetchWebContent("https://www.joinquant.com/help/data/stock", maxChars=8000)
// 多引擎搜索
search("聚宽 get_all_securities date 退市", limit=5)
```

> ★2026-08实测: firecrawl 云端(`mcp.firecrawl.dev`, 海外)被聚宽拒(返回"Service Unavailable in Your Region"); **本地 websearch(open-websearch, 本地运行走本地出口)成功访问聚宽官网**。

### 已确认可从 `help/data/stock` 查到的 API

| 函数 | 包含信息 |
|------|---------|
| `get_price` | 完整参数、返回值（DataFrame/Panel）、示例 |
| `get_fundamentals` | query/filter/date/statDate 用法，示例 |
| `get_all_securities` | types 参数、返回值字段 |
| `get_security_info` | 参数、返回对象属性 |
| `get_index_stocks` | 参数、研究/回测默认值差异 |
| `history` / `attribute_history` | 完整参数、df 选项 |
| `get_extras` | is_st / futures 等 info 选项 |
| `get_money_flow` | 资金流向字段表 |
| `get_mtss` | 融资融券字段表 |

---

## WebFetch 使用方式

```javascript
// 内置工具，无需额外配置（但非原生 Claude 模型可能不可用）
WebFetch("https://www.joinquant.com/help/data/stock", "提取 get_price 的参数列表和返回值类型")
```

**注意：** ⚠️firecrawl 走海外出口被聚宽拒(2026-08实测); 本地 websearch(open-websearch)走本地出口可访问聚宽官网; WebFetch 未经聚宽官网实测。
