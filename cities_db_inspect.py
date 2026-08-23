#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cities_db_inspect.py · GeographyAdvisor Phase 0.1 资产盘点脚本

目的:盘点 Defense/cities.db 当前覆盖度,作为 Phase 0 城市库补全的依据。
输出:Markdown 报告(stdout),可直接贴入 .plan/ 或日报。

用法:
  python3 cities_db_inspect.py                          # 默认读 ../Defense/cities.db
  python3 cities_db_inspect.py /path/to/cities.db       # 指定 DB 路径
  python3 cities_db_inspect.py --json                   # JSON 输出

不做写操作。纯只读盘点。
"""
from __future__ import annotations
import sqlite3
import sys
import json
from collections import Counter, defaultdict
from pathlib import Path

# 默认 DB 路径:GeographyWeb 上一层的 Defense/cities.db
DEFAULT_DB = Path(__file__).parent.parent.parent / "Defense" / "cities.db"


def pct(n: int, total: int) -> str:
    return f"{100 * n / total:.1f}%" if total else "—"


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        sys.exit(f"❌ DB not found: {db_path}\n   传入正确路径:python3 cities_db_inspect.py /path/to/cities.db")
    return sqlite3.connect(str(db_path))


def inspect(db_path: Path) -> dict:
    con = connect(db_path)
    cur = con.cursor()
    report: dict = {"db": str(db_path), "tables": {}}

    # 1) 表清单
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )]
    report["tables_list"] = tables

    # 2) entity 总览
    entities = [dict(zip(
        ["code", "name", "type", "parent", "desc_short", "created_at", "updated_at", "metrics"],
        r
    )) for r in cur.execute("SELECT * FROM entity")]
    report["entity_count"] = len(entities)
    report["city_count"] = sum(1 for e in entities if e["type"] == "city")
    report["company_count"] = sum(1 for e in entities if e["type"] == "company")

    # 3) entity 详情
    report["entities"] = entities

    # 4) 指标分布
    metrics_dist = cur.execute("""
        SELECT metric_name, COUNT(*) AS n,
               COUNT(DISTINCT entity_code) AS cities,
               MIN(metric_value) AS vmin, MAX(metric_value) AS vmax
        FROM entity_metrics_history
        GROUP BY metric_name
        ORDER BY n DESC
    """).fetchall()
    report["metrics_dist"] = [
        {"name": r[0], "rows": r[1], "cities": r[2], "min": r[3], "max": r[4]}
        for r in metrics_dist
    ]

    # 5) symbol 按 kind / category
    kind_dist = cur.execute("""
        SELECT kind, COUNT(*) FROM entity_symbol GROUP BY kind ORDER BY 2 DESC
    """).fetchall()
    cat_dist = cur.execute("""
        SELECT category, COUNT(*) FROM entity_symbol GROUP BY category ORDER BY 2 DESC
    """).fetchall()
    report["symbol_kind"] = [{"kind": k, "n": n} for k, n in kind_dist]
    report["symbol_category"] = [{"category": c, "n": n} for c, n in cat_dist]
    report["symbol_total"] = sum(n for _, n in kind_dist)

    # 6) 字段覆盖率
    cities = [e for e in entities if e["type"] == "city"]
    if cities:
        fields = ["name", "parent", "desc_short", "created_at", "updated_at", "metrics"]
        report["field_coverage"] = {
            f: f"{sum(1 for c in cities if c[f])}/{len(cities)} ({pct(sum(1 for c in cities if c[f]), len(cities))})"
            for f in fields
        }

    # 7) Phase 0 目标差距
    report["phase0_target"] = {
        "目标城市数": 200,
        "实际城市 entity 数": report["city_count"],
        "差距": 200 - report["city_count"],
    }

    con.close()
    return report


def render_md(r: dict) -> str:
    lines = []
    lines.append(f"# cities.db 资产盘点报告")
    lines.append("")
    lines.append(f"- **DB 路径**:`{r['db']}`")
    lines.append(f"- **表清单**:{', '.join(r['tables_list'])}")
    lines.append("")

    # 总览
    lines.append("## 一、Entity 总览")
    lines.append("")
    lines.append(f"| 类型 | 数量 |")
    lines.append(f"|---|---|")
    lines.append(f"| city(城市) | {r['city_count']} |")
    lines.append(f"| company(公司) | {r['company_count']} |")
    lines.append(f"| **合计** | **{r['entity_count']}** |")
    lines.append("")

    # 城市清单
    cities = [e for e in r["entities"] if e["type"] == "city"]
    if cities:
        lines.append("## 二、城市清单")
        lines.append("")
        lines.append("| code | name | parent | desc_short | metrics |")
        lines.append("|---|---|---|---|---|")
        for c in cities:
            d = c["desc_short"] or "—"
            m = "有" if c["metrics"] else "空"
            lines.append(f"| {c['code']} | {c['name']} | {c['parent']} | {d} | {m} |")
        lines.append("")

    # 指标
    if r.get("metrics_dist"):
        lines.append("## 三、Metrics 分布")
        lines.append("")
        lines.append("| metric_name | 行数 | 覆盖城市 | min | max |")
        lines.append("|---|---|---|---|---|")
        for m in r["metrics_dist"]:
            lines.append(f"| {m['name']} | {m['rows']} | {m['cities']} | {m['min']} | {m['max']} |")
        lines.append("")

    # Symbol
    if r.get("symbol_total"):
        lines.append("## 四、Symbol 分布")
        lines.append("")
        lines.append(f"**总计 {r['symbol_total']} 条 symbol**,按 kind:")
        lines.append("")
        lines.append("| kind | 数量 |")
        lines.append("|---|---|")
        for k in r["symbol_kind"]:
            lines.append(f"| {k['kind']} | {k['n']} |")
        lines.append("")
        lines.append("按 category:")
        lines.append("")
        lines.append("| category | 数量 |")
        lines.append("|---|---|")
        for c in r["symbol_category"]:
            lines.append(f"| {c['category']} | {c['n']} |")
        lines.append("")

    # 字段覆盖
    if r.get("field_coverage"):
        lines.append("## 五、城市字段覆盖率")
        lines.append("")
        lines.append("| 字段 | 覆盖 |")
        lines.append("|---|---|")
        for f, v in r["field_coverage"].items():
            lines.append(f"| {f} | {v} |")
        lines.append("")

    # Phase 0 差距
    t = r["phase0_target"]
    lines.append("## 六、Phase 0 目标差距")
    lines.append("")
    lines.append(f"- **目标**:{t['目标城市数']}+ 地级市入库")
    lines.append(f"- **实际**:{t['实际城市 entity 数']} 个 city entity")
    lines.append(f"- **差距**:还差 {t['差距']} 个城市")
    lines.append("")
    if t["差距"] > 0:
        lines.append("> → 下一阶段:Phase 0.2 批量入库 31 省会 + 重点旅游城市,优先补 **气候 / 方言 / 特产 / 非遗** 字段。")
    lines.append("")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    json_mode = "--json" in args
    args = [a for a in args if a != "--json"]

    db_path = Path(args[0]) if args else DEFAULT_DB
    r = inspect(db_path)

    if json_mode:
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    else:
        print(render_md(r))


if __name__ == "__main__":
    main()
