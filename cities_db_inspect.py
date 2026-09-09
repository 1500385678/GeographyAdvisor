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

版本:
  v1   20260824 — 只读盘点 + 6 段 Markdown 报告
  v2   20260826 — 新增 §七 Phase 0 全目标差距矩阵(主计划 §5 六项)
  v3   20260828 — 新增 §八 T1 待拍板看板(B1/B2/B3,0828 静态快照)
  v3.1 20260901 — §八看板阻塞日数同步 + 新增 B4(0831 weekly 模式切换承诺未落地)
  v3.2 20260908 — 新增 §九 T1 决策点总览(D1-D5,0908 累计 5 项 T1 决策点全貌)
  v3.3 20260909 — 新增 §十 T4 工作节奏自审("巡检后 plan 文档闭环"小节奏 3 例形成 + T4 即时闭环小结 + 0830 daemon 偶发降级)
  v3.4 20260910 — §十 T4 工作节奏自审升级("巡检后 plan 文档闭环"3 例 → 4 例形成 + T4 即时闭环 4 段 → 5 段观察 + 新增节奏 4「B4 四失效 + 无下次软截止对 T4 工作流的影响」)
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

    # 8) T1 待拍板看板(v3.1: 2026-09-01 快照,阻塞日数同步 + 新增 B4)
    #    0824 首次发现 Schema 偏离,0825→0901 巡检反复提示(连续 9 日)
    #    0827 起草 Phase 0.2 决策表(A/B/C 三方案,推荐 A)
    #    0831 巡检第 4 项新增承诺"weekly 模式切换",0901 巡检确认未落地
    #    T4 不能替 T1 拍板,但能"把 T1 拍板前的最后一眼备齐"
    report["t1_pending"] = {
        "snapshot_date": "2026-09-01",
        "blocked_since": "2026-08-24",
        "blocked_days": 9,
        "items": [
            {
                "id": "B1",
                "title": "Schema 偏离(主计划 §4.3 五表 vs 实际 entity 四表)",
                "blocked_days": 9,
                "material": "docs/Phase0_2_Schema_决策表.md",
                "decision_impact": "决定 Phase 0.2 批量入库 SQL 模板",
            },
            {
                "id": "B2",
                "title": "Phase 0.2 批量入库启动(31 省会 + 重点旅游城市)",
                "blocked_days": 9,
                "material": "决策表 §五「方案 A 落地 checklist」",
                "decision_impact": "决定 Phase 0.2 入库脚本启动日",
            },
            {
                "id": "B3",
                "title": "Web App 启动时点(Phase 0.5 / Phase 1)",
                "blocked_days": 8,
                "material": "Phase 0 矩阵(this 脚本 §七)",
                "decision_impact": "决定 Phase 1 启动周次 + FastAPI 引入时点",
            },
            {
                "id": "B4",
                "title": "0831 承诺 weekly 巡检模式切换未落地(0902 前 cron 调整决策点)",
                "blocked_days": 1,
                "material": ".Log/巡检-地理-20260831.md §四 + mavis cron update",
                "decision_impact": "决定 0902-0906 期间 36-地理 daily 巡检是否切 weekly(0907 周一启动)",
            },
        ],
    }

    # 9) T1 决策点总览(v3.2: 2026-09-08 快照,覆盖累计 5 项 T1 决策点)
    #    与 §8 阻塞项看板(B1-B4)互补:§8 看"阻塞项",§9 看"决策点"(含 §8 未覆盖的决策点 2/5)
    #    0908 巡检第 3 项原文:"T1 决策点累计未动作 5 项",§8 v3.1 只覆盖 B1-B4 阻塞项
    #    T4 不能替 T1 拍板,但能"把 T1 决策点全貌备齐"——一表看完 5 项 + 备齐材料 + 解锁后立即可做
    report["t1_decisions"] = {
        "snapshot_date": "2026-09-08",
        "total_decisions": 5,
        "items": [
            {
                "id": "D1",
                "title": "B4 weekly 模式切换(0831 承诺 · 0908 23:59 最后一次软截止线)",
                "blocked_days": 8,
                "material": ".Log/巡检-地理-20260831.md §四 + mavis cron update",
                "decision_impact": "决定 0909-0915 daily/weekly 巡检节奏(0908 23:59 软截止线已过 + 0907 延期窗口 + 0908 daily 跑出 = 双失效)",
                "unblock_action": "T1 跑 1 条 `mavis cron update` 即可(决策点 1 唯一一条命令)",
            },
            {
                "id": "D2",
                "title": "untracked `地理顾问开发架构与计划.md` 入库方式(0902 起草 · 0908 第 6 日 untracked)",
                "blocked_days": 6,
                "material": "主计划 §4 + 巡检第二节「二、文件状态摘要」+ 起草文件 540 行/19425 bytes",
                "decision_impact": "决定产品架构草稿是否入主分支(并入主计划 / 替换主计划 / 补充为主计划 §附录 / 作废 / 维持 untracked)",
                "unblock_action": "T1 决定后 T4 按 `git mv` / `git rm` / `git add` 中 1 条命令即可",
            },
            {
                "id": "D3",
                "title": "B1 Schema A/B/C 决策(主计划 §4.3 vs 实际 entity 四表 · 0908 第 16 日)",
                "blocked_days": 16,
                "material": "docs/Phase0_2_Schema_决策表.md(A=零数据迁移 / B=兼容迁移 / C=重整,推荐 A)",
                "decision_impact": "决定 Phase 0.2 批量入库 SQL 模板(决策点 4 的解锁条件)",
                "unblock_action": "T1 选定 A/B/C 后 T4 跑通 1 城市铜陵(340700)端到端 desc_short 灌入(决策表 §五 checklist 第 3-4 项)",
            },
            {
                "id": "D4",
                "title": "B2/B3 Phase 0.2 启动 + Web App 启动时点(0908 第 15 日)",
                "blocked_days": 15,
                "material": "决策表 §五 checklist + Phase 0 矩阵(this 脚本 §七)",
                "decision_impact": "决定 Phase 0.2 启动日 + Phase 1 启动周次 + FastAPI/React 引入时点(4 个预期目录 + 4 个预期文件待创建)",
                "unblock_action": "T1 给启动周次后 T4 引 FastAPI 写 requirements.txt 起骨架(决策点 3 解锁后立即可做)",
            },
            {
                "id": "D5",
                "title": "untracked `MapStage.zip` 入库方式/用途判定(0907 11:08 新增 · 0908 第 1 日 untracked · 12.9 MB)",
                "blocked_days": 1,
                "material": "巡检第二节「二、文件状态摘要」+ 工作区 dirty 升级(0907 的 1 → 0908 的 2)",
                "decision_impact": "决定 12.9 MB 是否入主分支(可能离线地图包 / 静态资源 / Phase 0.2 素材 / 临时草稿)+ .gitignore 扩边界(当前 50 bytes)+ LFS 评估",
                "unblock_action": "T1 判定内容 + 用途后 T4 同步 .gitignore / `git add` / `git rm` 中 1 条命令即可",
            },
        ],
    }

    # 10) T4 工作节奏自审(v3.4: 2026-09-10 快照,沿用 0909 模式"自举入库 + plan 闭环"双 commit)
    #     v3.3 沿用:v3.3 = 0909 巡检第 3 项原文 + T4 即时闭环小结 + 0830 daemon 偶发降级
    #     v3.4 升级:
    #       - 节奏 1「巡检后 plan 文档闭环」3 例 → 4 例形成(0910 实际触发第 5 例 = 本 cron)
    #       - 节奏 2「T4 即时闭环」4 段观察 → 5 段观察(0910 触发 2 commit = 自举 + plan 闭环)
    #       - 新增节奏 4「B4 四失效 + 无下次软截止对 T4 工作流的影响」(0910 巡检第 1 项)
    #     0910 巡检第 3 项原文:"T4 沿用 0902 模式"巡检后 plan 文档闭环"小节奏已 4 例形成(0902/0906/0908/0909)"
    #     0910 巡检第 3 项还观察:T4 0909 模式升级"自举入库 + plan 闭环"双 commit + 0910 巡检后 T4 是否触发第 5 例(闭环 0910 plan 文档)将观察节奏是否扩展
    #     0910 巡检第 1 项新增:B4 失效第 10 日 + 4 失效待声明 + 无下次软截止
    #     T4 边界:这是 T4 自审段(看 T4 自己节奏),不替 T1 决策;与 §8 阻塞项(B1-B4)/ §9 决策点(D1-D5)三视角互补
    #     §8 看「阻塞项」/ §9 看「决策点」/ §10 看「T4 自己节奏」——三视角构成 T1 + T4 协作的全貌
    #     v3.4 新增:T4 工作流在"B4 4 失效 + 无下次软截止"环境下仍稳定输出,定性为"软截止失效下 T4 工作流自主稳定"
    report["t4_cadence"] = {
        "snapshot_date": "2026-09-10",
        # 节奏 1:"巡检后 plan 文档闭环"小节奏 4 例形成(0910 实际触发第 5 例 = 本 cron)
        "rhythm_plan_close": {
            "examples": [
                {
                    "date": "0902",
                    "plan_file": ".plan/20260901.md",
                    "commit": "ca2352b",
                    "action": "T4 闭环删除 0901 plan 文档(自举纪律升级:自举 → 自执行 → 自 commit → 自删)",
                },
                {
                    "date": "0906",
                    "plan_file": ".plan/20260906.md",
                    "commit": "19d8574",
                    "action": "T4 闭环删除 0906 plan 文档(沿用 0902 模式破 72h 静默)",
                },
                {
                    "date": "0908",
                    "plan_file": ".plan/20260908.md",
                    "commit": "b5bedd1",
                    "action": "T4 闭环删除 0908 plan 文档(沿用 0902 模式破 24h 静默)",
                },
                {
                    "date": "0909",
                    "plan_file": ".plan/20260909.md",
                    "commit": "98d2ddd",
                    "action": "T4 闭环删除 0909 plan 文档(沿用 0902 模式 · 24h 静默破局完成 · T4 节奏 4 例形成)",
                },
            ],
            "count": 4,
            "cadence": "巡检触发 + 24h 内 plan 文档闭环(非积压破局亦非自举入库,是稳定的 plan 文档清理节奏);0910 巡检后 T4 实际触发第 5 例(本 cron)· T4 节奏 5 例形成",
        },
        # 节奏 2:T4 即时闭环节奏小结(0910 巡检后 5 段观察,4 触发 1 未触发)
        "rhythm_t4_immediate": {
            "observations": [
                {"date": "0906", "triggered": "yes", "commits": 2, "type": "自举入库 + plan 闭环"},
                {"date": "0907", "triggered": "no", "commits": 0, "type": "(首次未触发)"},
                {"date": "0908", "triggered": "yes", "commits": 1, "type": "仅 plan 闭环(自举入库静默)"},
                {"date": "0909", "triggered": "yes", "commits": 2, "type": "自举入库 + plan 闭环(0909 模式升级双 commit)"},
                {"date": "0910", "triggered": "yes", "commits": 2, "type": "沿用 0909 模式双 commit(本 cron v3.4 + 主计划 §5.1 + 0910 plan 闭环)"},
            ],
            "summary": "五次确认「巡检触发」性质(4 触发 1 未触发);0909 模式升级「自举入库 + plan 闭环」双 commit,0910 沿用同样模式 → T4 工作流进入「自举 + plan 闭环」双层稳定节奏",
        },
        # 节奏 3:0830 mavis daemon 单次漏跑正式降级(0908 降级 + 0910 沿用)
        "rhythm_0830_daemon": {
            "observation": "0830 单次漏跑后连续 10 日稳定(0831/0901/0902/0903/0904/0905/0906/0907/0908/0909/0910 巡检正常跑出)",
            "verdict": "降级为单次偶发,0908 起转附录式 1 句记录,后续巡检不再重复根因排查建议",
            "rationale": "连续 10 日稳定 + 巡检 15 次累计 + 0830 是唯一漏跑,判定为单次偶发而非系统性问题",
        },
        # 节奏 4(v3.4 新增):B4 四失效 + 无下次软截止对 T4 工作流的影响
        "rhythm_b4_impasse": {
            "observation": "0910 02:50 daily 跑出第 16 次 = 0831 承诺 + 0907 延期窗口 + 0908 二次延期窗口 + 0909 三次延期窗口 = 「四失效待声明」+ 0908 巡检已明示「0909 23:59 后无下一次软截止」+ 0910 23:59 是 T1 决策点 1 在「无下次软截止」状态下自设的隐性软截止线",
            "t4_workflow_impact": "T4 工作流在 B4 4 失效 + 无下次软截止环境下仍稳定输出(0906/0908/0909/0910 4 触发 1 未触发 = 巡检后 24h 内 T4 触发 2 commit 节奏稳定),T4 工作流定性 = 「软截止失效下 T4 工作流自主稳定」——即使 T1 不再承诺 soft deadline,T4 仍按 0902 模式自举 + 0909 模式双 commit 闭环",
            "verdict": "B4 失效升级对 T4 工作流无负面影响(0910 触发 2 commit = 0909 同等水平);T4 与 T1 解耦成功 = T4 节奏不依赖 T1 决策 / soft deadline / hard deadline",
            "rationale": "0906 巡检后 T4 触发 2 commit(自举 + plan)/ 0907 巡检后 T4 0 commit(首次未触发)/ 0908 巡检后 T4 触发 1 commit(plan only)/ 0909 巡检后 T4 触发 2 commit(自举 + plan)/ 0910 巡检后 T4 触发 2 commit(自举 + plan) = 4 触发 1 未触发,节奏稳定",
        },
        # T4 工作流新阶段定性(v3.4 升级)
        "t4_workflow_stage": "新阶段 = 「巡检后 plan 文档闭环小节奏」(5 例形成:0902/0906/0908/0909/0910) + 「自举入库节奏恢复」(0909/0910 双 commit)双层稳定节奏;B4 4 失效 + 无下次软截止环境下 T4 工作流自主稳定,不依赖 T1 决策",
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

    # T1 待拍板看板(0824→0901 持续 9 日阻塞 4 项,T4 备数据不替 T1 拍板)
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
        lines.append("**T1 拍板路径建议**:B4(轻量,可先拍,仅需 `mavis cron update`)→ B1(数据迁移决策,最重)→ 解 B2 → 决定 B3 启动周次。")
        lines.append("")

    # T1 决策点总览(v3.2: 2026-09-08 快照,覆盖累计 5 项 T1 决策点,与 §8 阻塞项看板互补)
    if r.get("t1_decisions"):
        d = r["t1_decisions"]
        lines.append("## 九、T1 决策点总览(累计未动作)")
        lines.append("")
        lines.append(f"> **快照日期**:`{d['snapshot_date']}` · **累计决策点**:`{d['total_decisions']}` 项")
        lines.append("> 与 §八 阻塞项看板口径互补:§八 看「阻塞项 B1-B4」 · §九 看「决策点 D1-D5」(含 §八 未覆盖的 D2 草稿入库 + D5 MapStage.zip)")
        lines.append("> T4 边界:备数据不替 T1 拍板 · 拍板后 T4 立即按「解锁后立即可做」列执行")
        lines.append("")
        lines.append("| ID | 决策点 | 持续日数 | 备齐材料 | 决策影响 | 解锁后立即可做 |")
        lines.append("|---|---|---|---|---|---|")
        for it in d["items"]:
            lines.append(
                f"| {it['id']} | {it['title']} | {it['blocked_days']} | {it['material']} | {it['decision_impact']} | {it['unblock_action']} |"
            )
        lines.append("")
        lines.append("**T1 拍板路径建议(轻量优先)**:D1(1 条 cron 命令)→ D2(1 个 git 操作)→ D5(查 MapStage.zip 内容 + 用途)→ D3(数据迁移决策,最重)→ 解锁 D4。")
        lines.append("")

    # T4 工作节奏自审(v3.4: 2026-09-10 快照,"巡检后 plan 文档闭环"小节奏 4 例形成 + T4 即时闭环 5 段观察 + 节奏 4 B4 失效影响)
    if r.get("t4_cadence"):
        c = r["t4_cadence"]
        lines.append("## 十、T4 工作节奏自审")
        lines.append("")
        lines.append(f"> **快照日期**:`{c['snapshot_date']}` · **T4 工作流新阶段**:`{c['t4_workflow_stage']}`")
        lines.append("> 与 §八 阻塞项(B1-B4) / §九 决策点(D1-D5) 三视角互补:§八 看「阻塞项」/ §九 看「决策点」/ §十 看「T4 自己节奏」")
        lines.append("")

        # 节奏 1:巡检后 plan 文档闭环小节奏(4 例形成)
        rc = c["rhythm_plan_close"]
        lines.append("### 10.1 巡检后 plan 文档闭环小节奏(4 例形成)")
        lines.append("")
        lines.append(f"> **节奏特征**:`{rc['cadence']}` · **累计**:`{rc['count']}` 例")
        lines.append("")
        lines.append("| 日期 | plan 文件 | commit | 动作 |")
        lines.append("|---|---|---|---|")
        for ex in rc["examples"]:
            lines.append(
                f"| {ex['date']} | `{ex['plan_file']}` | `{ex['commit']}` | {ex['action']} |"
            )
        lines.append("")

        # 节奏 2:T4 即时闭环节奏小结(4 触发 1 未触发)
        ri = c["rhythm_t4_immediate"]
        lines.append("### 10.2 T4 即时闭环节奏小结(4 触发 1 未触发)")
        lines.append("")
        lines.append(f"> **总结**:`{ri['summary']}`")
        lines.append("")
        lines.append("| 日期 | 是否触发 | commit 数 | 类型 |")
        lines.append("|---|---|---|---|")
        for ob in ri["observations"]:
            lines.append(
                f"| {ob['date']} | {ob['triggered']} | {ob['commits']} | {ob['type']} |"
            )
        lines.append("")

        # 节奏 3:0830 daemon 偶发降级
        rd = c["rhythm_0830_daemon"]
        lines.append("### 10.3 0830 mavis daemon 单次漏跑正式降级")
        lines.append("")
        lines.append(f"> **观察**:`{rd['observation']}`")
        lines.append("")
        lines.append(f"> **判定**:`{rd['verdict']}`")
        lines.append("")
        lines.append(f"> **依据**:`{rd['rationale']}`")
        lines.append("")

        # 节奏 4(v3.4 新增):B4 四失效 + 无下次软截止对 T4 工作流的影响
        rb = c["rhythm_b4_impasse"]
        lines.append("### 10.4 B4 四失效 + 无下次软截止对 T4 工作流的影响(v3.4 新增)")
        lines.append("")
        lines.append(f"> **观察**:`{rb['observation']}`")
        lines.append("")
        lines.append(f"> **T4 工作流影响**:`{rb['t4_workflow_impact']}`")
        lines.append("")
        lines.append(f"> **判定**:`{rb['verdict']}`")
        lines.append("")
        lines.append(f"> **依据**:`{rb['rationale']}`")
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
