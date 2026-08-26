# Phase 0.2 Schema 决策表

> 给 T1 拍板用 · 起草日 2026-08-27 · 起草人 36-地理 T4
> 解决:主计划 §4.3 SQL vs `Defense/cities.db` 实际 schema 偏离(0824 首次发现,0825/0826/0827 三日巡检反复提示,未拍板)

---

## 一、问题陈述(事实)

### 1.1 主计划 §4.3 写的是"五表"

`项目开发计划.md` §4.3 定义了 5 张表:

| # | 表 | 用途 |
|---|---|---|
| 1 | `cities` | 城市主表 |
| 2 | `city_profiles` | 城市档案(overview/history/culture/food/travel_notes) |
| 3 | `cultural_symbols` | 非遗/老字号 |
| 4 | `attractions` | 景点 |
| 5 | `data_snapshots` | 数据快照(时序) |

### 1.2 `Defense/cities.db` 实际是"四表 + 多态"

实测 `cities_db_inspect.py` 0827 重跑输出:`entity` / `entity_metrics_history` / `entity_symbol` / `entity_relation`(另外还有 `sqlite_sequence`)。

关键差异:
- **多态 entity 表**:`type` 字段区分 `city` / `company`,**一表覆盖多实体类型**。当前 4 个 entity(3 city + 1 company)共存。
- **没有 city_profiles 拆表**:城市档案的"概述/历史/文化/美食/旅行"5 段,主计划想单表,实际没建。
- **没有 attractions 拆表**:景点数据目前用 `entity_symbol(category='地标')` 收纳,共 5 条。
- **没有 data_snapshots 拆表**:时序数据走 `entity_metrics_history`,但**每城市每指标仅 1 个时间点**(实测 3 城市 × 9 指标 ≈ 27 行,0825/0826/0827 报告一致)。
- **多了 entity_relation 表**:实体关系(暂未实测数据),主计划未提及。

### 1.3 偏离持续时间

- 0824 首次发现(.plan/20260824.md · Phase 0.1 增量段)
- 0825 巡检第 1 次报(`.Log/巡检-地理-20260825.md` §四)
- 0826 巡检第 2 次报(`.Log/巡检-地理-20260826.md`)
- 0827 巡检第 3 次报(`.Log/巡检-地理-20260827.md`)· "**直接影响 Phase 0.2 批量入库的 SQL 模板设计**"

---

## 二、三种方案(选项 A / B / C)

### 方案 A · 改主计划对齐实际 schema(推荐)

**做法**:
- 主计划 §4.3 改写为 4 表 + 多态 entity,与 `Defense/cities.db` 一致
- `city_profiles` 字段收编进 `entity.desc_short` + 新增 `entity_profile` 字段(预留 JSON 列存 5 段)
- `attractions` 复用 `entity_symbol` + 新增 `category='地标'`
- `data_snapshots` 沿用 `entity_metrics_history`,只需补多时间点

**优点**:
- ✅ 零数据迁移,直接动工 Phase 0.2 批量入库
- ✅ 现有 `cities_db_inspect.py` 可继续作为只读验证
- ✅ 多态 entity 兼容未来扩展(company、景区、大学、机场)
- ✅ 与 `_GeographyLib/` 已沉淀的城市档案(`Defense/铜陵/` 等)并行不悖
- ✅ `query_city.py` / `query_entity.py` 不动

**缺点**:
- ❌ 主计划 §4.3 SQL 文本需大改(影响文档)
- ❌ 多态 entity 不符合 3NF(范式纯化党会皱眉)
- ❌ 新人看 schema 需要"先懂多态"再上手

**适配场景**:
- 张勇已接受多态设计(实测 Defense/cities.db 是这模式)
- Phase 0.2 批量入库 200+ 城市是最高优先
- Phase 1 起步阶段,稳 > 范式美

---

### 方案 B · 改实际 schema 对齐主计划

**做法**:
- 在 `Defense/cities.db` 新建 `cities` / `city_profiles` / `attractions` / `data_snapshots` 5 表
- 写迁移脚本把 entity 4 条数据从 entity 表 → 5 表
- 旧 entity 表保留(标记 deprecated)

**优点**:
- ✅ 主计划 §4.3 SQL 文本不动
- ✅ 范式干净,新人易上手
- ✅ 跟主流地理信息系统设计(PGIS、PostGIS)对齐

**缺点**:
- ❌ 需要写迁移脚本 + 回归测试
- ❌ 多态信息(company 实体)要拆出去,新建 `companies` 表
- ❌ 现有 `cities_db_inspect.py` 需大改
- ❌ 触发 Defense/cities.db 写操作(.plan/20260826.md 边界:"❌ 不动 `Defense/cities.db`")
- ❌ Phase 0.2 起步时间延后 1-2 周(迁移 + 验证)

**适配场景**:
- 范式美 > 上线速度
- 有 DBA 角色长期维护 schema
- 长期规划 ≥ 半年

---

### 方案 C · 双库并跑(短期中间态)

**做法**:
- 保留 `Defense/cities.db`(只读,作为 source of truth)
- 新建 `WebApp/web.db`,5 表按主计划 §4.3 建
- 写 ETL 脚本:`web.db ← cities.db` 每日同步
- Phase 0.2 批量入库直接写 `web.db`

**优点**:
- ✅ 主计划 §4.3 文本不动
- ✅ Defense/cities.db 不动
- ✅ 5 表结构清晰

**缺点**:
- ❌ 两库要长期维护一致性
- ❌ 增加 ETL 复杂度
- ❌ 增加 1 个 DB 文件,违反"1 DB 集中组织"哲学
- ❌ 写 ETL 本身需要先定 schema,还是回到 A/B 选择
- ❌ Defense 和 WebApp 同一份数据走两套 SQL,新人两倍学习成本

**适配场景**:
- 极少见,除非 Defense 是"只读 archive"而 WebApp 是"读写主库",且两边数据所有权不同

---

## 三、方案对比矩阵

| 维度 | A · 改主计划 | B · 改 schema | C · 双库 |
|---|---|---|---|
| **数据迁移** | 零 | 需迁移脚本 | 需 ETL |
| **动 Defense/cities.db** | ❌ 否 | ✅ 是(写) | ❌ 否 |
| **改主计划 §4.3** | ✅ 是 | ❌ 否 | ❌ 否 |
| **改 cities_db_inspect.py** | 极小(只补 JSON 字段解读) | 大改 | 中改 |
| **Phase 0.2 启动时间** | 当周 | 1-2 周后 | 1 周后(ETL 先写) |
| **新人学习成本** | 中(多态) | 低 | 高(两库) |
| **范式纯度** | 中 | 高 | 中 |
| **长期扩展性** | 高(多态易扩) | 中(再加表) | 中 |
| **与现有 _GeographyLib 一致性** | 高(都已多态) | 低 | 中 |
| **T4 落地复杂度** | **低** | 高 | 高 |

---

## 四、推荐:方案 A(理由 3 条)

1. **零数据迁移,Phase 0.2 当周可启动**:这是 36-地理当前最缺的东西——"打破 3 日零推进"。方案 A 让批量入库 SQL 直接基于 entity 表写,无需迁移。
2. **Defense/cities.db 不动**:沿用 T4 .plan/20260826.md 的边界纪律(❌ 不动 `Defense/cities.db`)。方案 B 必破,方案 C 走 ETL 也破。
3. **多态 entity 是张勇设计语言**:实测 36-地理 Defense/cities.db 已是多态 + 其他 36 个行业的 Defense/*.db 多半也是多态(参考 36 架构约定)。改主计划对齐实际,比改实际对齐主计划更尊重既成事实。

---

## 五、方案 A 落地 checklist(给 T4 拍板后用)

> T1 拍板方案 A 后,T4 可立即执行:

- [ ] `项目开发计划.md` §4.3 改写为"4 表 + 多态 entity",附与原版的差异对照
- [ ] `cities_db_inspect.py` §7 Phase 0 矩阵里 0.2 行的"actual"列,加 desc_short 字段补全进度
- [ ] 新建 `tools/import_city_profile.py`:从 `_GeographyLib/02_地理分支与特点/` 摘 desc_short 灌入 `entity.desc_short`
- [ ] 跑通 1 个城市铜陵(340700)端到端,做模板
- [ ] 跑通 3 城市(铜陵/上海/北京),把 desc_short 覆盖率从 0/3 推到 3/3
- [ ] 评估批量灌 31 省会城市的脚本模板(每日 T4 推 3-5 城市)

**不做**:
- ❌ 不动 `Defense/cities.db` 的 entity 表结构(只往 entity.desc_short 写)
- ❌ 不批量一次灌 200 城市(分 6 批,每天 T4 推一批)
- ❌ 不引 FastAPI / requirements.txt(等 Phase 1 启动再引)

---

## 六、变更记录

| 日期 | 变更 | 作者 |
|---|---|---|
| 2026-08-27 | 新建本决策表(3 方案对比 + 推荐 A) | 36-地理 T4 |
| (待 T1 拍板) | 在 §四 标注"已选 A/B/C + 决定日期" | T1 |
