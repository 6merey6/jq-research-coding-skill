# Fallback 文档 URL — jq-docs MCP 不可用时使用

jq-docs MCP 需要从 GitHub 拉取，在大陆无代理时不可用。本文档记录替代方案。

## 优先级

1. jq-docs MCP (`lookup_function` / `search_docs`)
2. firecrawl MCP (`firecrawl_scrape`, 需额外配置，支持完整页面抓取)
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

## firecrawl 使用方式

### 配置（非必需，询问 scope + "不配置"选项）

```bash
claude mcp add --scope <project|user|local> firecrawl -- npx -y @anthropic-ai/mcp-server-firecrawl
```

### 使用方法

```javascript
// 抓取完整页面
firecrawl_scrape("https://www.joinquant.com/help/data/stock", formats=["markdown"])

// 结果缓存约1小时，相同 URL 可复用
// 页面内容通常较大（20万+字符），提取所需部分即可
```

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

**注意：** 大陆网络环境可能导致 WebFetch 和 firecrawl 都不稳定。
