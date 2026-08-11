#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聚宽 API 文档查询 CLI(纯 Python 标准库,零依赖,完全离线)。

数据来源: 本目录下的 jq_knowledge.db(SQLite,来自 jiaweizhang1995/jq-docs-mcp,MIT)。
替代 jq-docs MCP 服务器 —— skill 不需要注册任何 MCP 即可查询聚宽 API 文档。

用法:
  python query_jq_docs.py lookup  <函数名>      完整函数文档(签名/参数/返回/示例)
  python query_jq_docs.py search  <关键词>      中英文关键词搜索(函数名/中文名/描述/签名)
  python query_jq_docs.py sections              列出所有文档分类
  python query_jq_docs.py section <分类名>      某分类下所有函数
  python query_jq_docs.py search-in-section <关键词> <分类名>   在指定分类内搜索
  python query_jq_docs.py functions             列出全部函数(按分类分组)
  python query_jq_docs.py table   <表名>        数据表字段定义(供 get_fundamentals 用)

输出为 Markdown 文本(与上游 MCP 服务器 _format_* 一致的格式)。
"""
import argparse
import sqlite3
import sys
from pathlib import Path

_DB = Path(__file__).resolve().parent / "jq_knowledge.db"


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------------------------------------------------
# 格式化(与上游 server.py 输出一致,便于模型解析)
# ----------------------------------------------------------------------
def _fmt_function_doc(row, params, return_attrs) -> str:
    lines = [f"## Function: {row['function_name']}"]
    if row["chinese_name"]:
        lines.append(f"**Chinese Name:** {row['chinese_name']}")
    lines.append(f"**Section:** {row['section']}")
    if row["call_signature"]:
        lines.append(f"\n### Signature\n`{row['call_signature']}`")
    if row["description"]:
        lines.append(f"\n### Description\n{row['description']}")
    if params:
        lines.append("\n### Parameters")
        lines.append("| Name | Type | Required | Description |")
        lines.append("|------|------|----------|-------------|")
        for p in params:
            req = "Yes" if p["is_required"] else "No"
            lines.append(f"| {p['param_name']} | {p['param_type'] or '-'} | {req} | {p['description'] or '-'} |")
    if row["return_type"]:
        lines.append(f"\n### Returns\n**Type:** {row['return_type']}")
    if return_attrs:
        lines.append("\n**Return Attributes:**")
        for a in return_attrs:
            lines.append(f"- `{a['attr_name']}` ({a['attr_type'] or '-'}): {a['description'] or '-'}")
    if row["example_code"]:
        lines.append(f"\n### Example\n```python\n{row['example_code']}\n```")
    return "\n".join(lines)


def _fmt_search(rows) -> str:
    lines = ["## Search Results", f"Found {len(rows)} result(s):", ""]
    for r in rows:
        lines.append(f"- **{r['function_name']}** ({r['chinese_name'] or '-'}) — {r['description'] or '-'} [{r['section']}]")
    return "\n".join(lines)


def _fuzzy_suggestions(conn, name: str, limit: int = 5) -> list:
    prefix = name[:4] if len(name) >= 4 else name
    rows = conn.execute(
        "SELECT function_name FROM api_docs WHERE function_name LIKE ? LIMIT ?",
        (f"{prefix}%", limit),
    ).fetchall()
    if rows:
        return [r["function_name"] for r in rows]
    return [r["function_name"] for r in conn.execute(
        "SELECT function_name FROM api_docs LIMIT ?", (limit,)
    ).fetchall()]


# ----------------------------------------------------------------------
# 子命令实现(对应上游 6 个 MCP 工具)
# ----------------------------------------------------------------------
def cmd_lookup(conn, name: str) -> str:
    row = conn.execute("SELECT * FROM api_docs WHERE function_name = ?", (name,)).fetchone()
    if row is None:
        sug = _fuzzy_suggestions(conn, name)
        hint = f"\nSimilar functions: {', '.join(sug)}" if sug else ""
        return f"Function '{name}' not found.{hint}"
    params = conn.execute(
        "SELECT param_name, param_type, is_required, description FROM api_params WHERE function_name = ?",
        (name,),
    ).fetchall()
    attrs = conn.execute(
        "SELECT attr_name, attr_type, description FROM api_return_attrs WHERE function_name = ?",
        (name,),
    ).fetchall()
    return _fmt_function_doc(row, params, attrs)


def cmd_search(conn, keyword: str) -> str:
    p = f"%{keyword}%"
    rows = conn.execute(
        """SELECT function_name, chinese_name, description, section FROM api_docs
           WHERE function_name LIKE ? OR chinese_name LIKE ? OR description LIKE ? OR call_signature LIKE ?
           LIMIT 20""",
        (p, p, p, p),
    ).fetchall()
    return f"No results found for '{keyword}'." if not rows else _fmt_search(rows)


def cmd_search_in_section(conn, keyword: str, section: str) -> str:
    p = f"%{keyword}%"
    rows = conn.execute(
        """SELECT function_name, chinese_name, description, section FROM api_docs
           WHERE section = ?
             AND (function_name LIKE ? OR chinese_name LIKE ? OR description LIKE ? OR call_signature LIKE ?)
           LIMIT 20""",
        (section, p, p, p, p),
    ).fetchall()
    if not rows:
        return f"No results found for '{keyword}' in section '{section}'."
    return _fmt_search(rows)


def cmd_sections(conn) -> str:
    rows = conn.execute("SELECT DISTINCT section FROM api_docs ORDER BY section").fetchall()
    return "\n".join(f"- {r['section']}" for r in rows)


def cmd_section(conn, section: str) -> str:
    rows = conn.execute(
        "SELECT function_name, chinese_name, description FROM api_docs WHERE section = ?",
        (section,),
    ).fetchall()
    if not rows:
        avail = ", ".join(r["section"] for r in conn.execute("SELECT DISTINCT section FROM api_docs").fetchall())
        return f"No functions found in section '{section}'.\nAvailable sections: {avail}"
    lines = [f"## Section: {section}", f"Found {len(rows)} function(s):", ""]
    for r in rows:
        lines.append(f"- **{r['function_name']}** ({r['chinese_name'] or '-'}) — {r['description'] or '-'}")
    return "\n".join(lines)


def cmd_functions(conn) -> str:
    rows = conn.execute("SELECT function_name, section FROM api_docs ORDER BY section, function_name").fetchall()
    grouped: dict = {}
    for r in rows:
        grouped.setdefault(r["section"], []).append(r["function_name"])
    lines = ["## Available Functions"]
    for s, names in grouped.items():
        lines.append(f"\n### {s} ({len(names)})")
        lines.extend(f"- {n}" for n in names)
    lines.append(f"\n**Total: {len(rows)} functions**")
    return "\n".join(lines)


def cmd_table(conn, table_name: str) -> str:
    rows = conn.execute(
        "SELECT column_name, column_type, meaning, description FROM table_columns WHERE table_name = ? ORDER BY column_name",
        (table_name,),
    ).fetchall()
    if not rows:
        avail = ", ".join(r["table_name"] for r in conn.execute(
            "SELECT DISTINCT table_name FROM table_columns ORDER BY table_name LIMIT 20"
        ).fetchall())
        return f"Table '{table_name}' not found.\nAvailable tables (first 20): {avail}"
    lines = [f"## Table: {table_name}", f"{len(rows)} column(s):", "",
             "| Column | Type | Meaning | Description |", "|--------|------|---------|-------------|"]
    for r in rows:
        lines.append(f"| {r['column_name']} | {r['column_type'] or '-'} | {r['meaning'] or '-'} | {r['description'] or '-'} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="query_jq_docs.py",
        description="聚宽 API 文档查询(纯本地 SQLite,零依赖)。",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_lookup = sub.add_parser("lookup", help="完整函数文档")
    p_lookup.add_argument("name", help="函数名,如 get_price")
    p_search = sub.add_parser("search", help="关键词搜索")
    p_search.add_argument("keyword", help="中英文关键词")
    sub.add_parser("sections", help="列出所有分类")
    p_section = sub.add_parser("section", help="某分类下函数")
    p_section.add_argument("section", help="分类名")
    p_sis = sub.add_parser("search-in-section", help="在指定分类内搜索")
    p_sis.add_argument("keyword", help="中英文关键词")
    p_sis.add_argument("section", help="分类名")
    sub.add_parser("functions", help="列出全部函数")
    p_table = sub.add_parser("table", help="数据表字段")
    p_table.add_argument("table_name", help="表名,如 FINANCE_INCOME_STATEMENT")

    args = parser.parse_args()
    # Windows 控制台可能 GBK,统一按 UTF-8 输出(便于 AI 读取)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    conn = _open()
    try:
        if args.cmd == "lookup":
            out = cmd_lookup(conn, args.name)
        elif args.cmd == "search":
            out = cmd_search(conn, args.keyword)
        elif args.cmd == "sections":
            out = cmd_sections(conn)
        elif args.cmd == "section":
            out = cmd_section(conn, args.section)
        elif args.cmd == "search-in-section":
            out = cmd_search_in_section(conn, args.keyword, args.section)
        elif args.cmd == "functions":
            out = cmd_functions(conn)
        elif args.cmd == "table":
            out = cmd_table(conn, args.table_name)
        else:
            parser.print_help()
            return 1
    finally:
        conn.close()
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
