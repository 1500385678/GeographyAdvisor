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

    # 7) Phase 0 目标差距(精简版,仅城市数)
    report["phase0_target"] = {
        "目标城市数": 200,
        "实际城市 entity 数": report["city_count"],
        "差距": 200 - report["city_count"],
    }

    # 8) Phase 0 全目标差距矩阵(主计划 §5 六项,逐项评估)
    #    各项阈值取自主计划 §5「Phase 0 资产盘点」原话,见 docstring
    phase0_items = [
        {
            "id": "0.1",
            "title": "写 cities_db_inspect.py(资产盘点脚本)",
            "status": "done",
            "actual": "cities_db_inspect.py 已交付,纯只读",
            "target": "可盘点脚本",
        },
        {
            "id": "0.2",
            "title": "补全缺失字段(气候/方言/特产/非遗)",
            "status": "in_progress" if report["city_count"] > 0 else "todo",
            "actual": f"desc_short {report.get('field_coverage', {}).get('desc_short', '0/0')}",
            "target": "5 字段全填(气候/方言/特产/非遗 + desc_short)",
        },
        {
            "id": "0.3",
            "title": "导入 88 城市档案(31 省会 + 重点旅游城市 + 铜陵等示例)",
            "status": "in_progress" if report["city_count"] >= 1 else "todo",
            "actual": f"{report['city_count']} city entity(当前:铜陵 340700 / 上海 310000 / 北京 110000)",
            "target": "88 城市档案 + cities.db city entity ≥ 88",
        },
        {
            "id": "0.4",
            "title": "文化符号库初版(国家级非遗 1500+ + 老字号 100+)",
            "status": "in_progress" if report["symbol_total"] >= 1 else "todo",
            "actual": f"{report['symbol_total']} symbol(类别:{', '.join(k['kind'] for k in report['symbol_kind']) or '无'})",
            "target": "国家级非遗 1500+ + 老字号 100+ + 方言专项",
        },
        {
            "id": "0.5",
            "title": "搭建 FastAPI 骨架 + /atlas /map 接口(只读查询)",
            "status": "todo",
            "actual": "项目根目录无 app.py / main.py / requirements.txt / 任何 FastAPI 文件",
            "target": "FastAPI 启动 + /atlas /map 只读端点 + curl 自检通过",
        },
        {
            "id": "0.6",
            "title": "飞书 Bot 接入'城市速查 + 旅行建议'两条流水线",
            "status": "todo",
            "actual": "36-地理 agent cron(每日 03:50)可代答,但 bot 接入未配置",
            "target": "feishu-channel.yaml + 城市速查 / 旅行建议 两个 intent 命中",
        },
    ]
    # 总结行:已完成 / 进行中 / 待办 计数
    summary = {"done": 0, "in_progress": 0, "todo": 0}
    for it in phase0_items:
        summary[it["status"]] = summary.get(it["status"], 0) + 1
    report["phase0_matrix"] = {
        "items": phase0_items,
        "summary": summary,
        "total": len(phase0_items),
    }

    # 8) T1 待拍板看板(2026-08-28 快照)
    #    0824 首次发现 Schema 偏离,0825/0826/0827/0828 巡检反复提示,
    #    0827 起草 Phase 0.2 决策表(A/B/C 三方案,推荐 A),0828 仍未拍板
    #    T4 不能替 T1 拍板,但能"把 T1 拍板前的最后一眼备齐"
    report["t1_pending"] = {
        "snapshot_date": "2026-08-28",
        "blocked_since": "2026-08-24",
        "blocked_days": 5,
        "items": [
            {
                "id": "B1",
                "title": "Schema 偏离(主计划 §4.3 五表 vs 实际 entity 四表)",
                "blocked_days": 5,
                "material": "docs/Phase0_2_Schema_决策表.md",
                "decision_impact": "决定 Phase 0.2 批量入库 SQL 模板",
            },
            {
                "id": "B2",
                "title": "Phase 0.2 批量入库启动(31 省会 + 重点旅游城市)",
                "blocked_days": 5,
                "material": "决策表 §五「方案 A 落地 checklist」",
                "decision_impact": "决定 Phase 0.2 入库脚本启动日",
            },
            {
                "id": "B3",
                "title": "Web App 启动时点(Phase 0.5 / Phase 1)",
                "blocked_days": 4,
                "material": "Phase 0 矩阵(this 脚本 §七)",
                "decision_impact": "决定 Phase 1 启动周次 + FastAPI 引入时点",
            },
        ],
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

    # Phase 0 全目标差距矩阵(主计划 §5 六项)
    if r.get("phase0_matrix"):
        m = r["phase0_matrix"]
        lines.append("## 七、Phase 0 全目标差距矩阵(主计划 §5)")
        lines.append("")
        lines.append(f"**汇总**:`done {m['summary']['done']} · in_progress {m['summary']['in_progress']} · todo {m['summary']['todo']}`(共 {m['total']} 项)")
        lines.append("")
        lines.append("| ID | 任务 | 状态 | 实际 | 目标 |")
        lines.append("|---|---|---|---|---|")
        status_emoji = {"done": "✅", "in_progress": "🟡", "todo": "⬜"}
        for it in m["items"]:
            lines.append(
                f"| {it['id']} | {it['title']} | {status_emoji.get(it['status'], it['status'])} | {it['actual']} | {it['target']} |"
            )
        lines.append("")
        lines.append("> 本段由 `cities_db_inspect.py` 自动生成,可贴入 `.Log/巡检-地理-YYYYMMDD.md` 与日报。")
        lines.append("> 阈值取自主计划 §5「Phase 0 资产盘点」原文,微调请同步主计划 + 脚本常量。")
        lines.append("")

    # T1 待拍板看板(0824→0828 持续 5+ 日阻塞 3 项,T4 备数据不替 T1 拍板)
    if r.get("t1_pending"):
        p = r["t1_pending"]
        lines.append("## 八、T1 待拍板看板")
        lines.append("")
        lines.append(f"> **快照日期**:`{p['snapshot_date']}` · **阻塞起始**:`{p['blocked_since']}` · **持续**:`{p['blocked_days']}` 日")
        lines.append("> T4 边界:备数据不替 T1 拍板 · 拍板后 T4 立即按决策表 §五 checklist 落地")
        lines.append("")
        lines.append("| ID | 阻塞项 | 持续日数 | 备齐材料 | 决策影响 |")
        lines.append("|---|---|---|---|---|")
        for it in p["items"]:
            lines.append(
                f"| {it['id']} | {it['title']} | {it['blocked_days']} | {it['material']} | {it['decision_impact']} |"
            )
        lines.append("")
        lines.append("**T1 拍板路径建议**:先 B1(零数据迁移选项)→ 解 B2 → 决定 B3 启动周次。")
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
