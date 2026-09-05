# GeographyAdvisor

> 36-地理-Geography 行业 Web 项目 · 内部代号 GeographyAdvisor

## 项目说明
基于张勇的 36 行业架构,GeographyAdvisor 是 地理-Geography 行业的 Web 端顾问产品。

## 同步
- GitHub: https://github.com/1500385678/GeographyAdvisor
- Gitee: https://gitee.com/architectzy/GeographyAdvisor

## 自动化
- T4 每日 02:00 检查项目并更新开发计划
- T5 每日 03:00 完成小步开发并 commit + push

## 项目状态快照

> 快照源:`.Log/巡检-地理-20260906.md`(0906 02:50 commit `cdeb2d5`)
> 快照粒度:Phase 进度 + 阻塞看板 + T1 决策点 + 工作区 dirty
> T1 拍板后请同步更新本段;T4 不替 T1 决策,只搬运巡检事实

### Phase 进度

| Phase | 状态 | 关键产物 | 阻塞 |
|---|---|---|---|
| **Phase 0 内容索引** | ✅ 完成 | `INDEX.md`(10 主题 9 文件 / 2226 行 / 59.6 KB) | 无 |
| **Phase 0.1 资产盘点** | ✅ 完成 | `cities_db_inspect.py` v3.1(含 §8 待拍板看板) | 无 |
| **Phase 0.2 批量入库** | ⏳ 待 T1 拍 B1 | `docs/Phase0_2_Schema_决策表.md`(A/B/C 三方案已起草) | B1 Schema 偏离 0824→0906 第 14 日 |
| **Phase 0.5 选型** | ⏳ 待 T1 拍 B3 | 选型未定(候选 FastAPI + React + Leaflet + ECharts) | B3 Web App 启动时点 0825→0906 第 13 日 |
| **Phase 1 Web App** | ⏳ 等 B3 解锁 | 0/7 checkbox 维持,`app/` `web/` `frontend/` `backend/` 均不存在 | 同 B3 |

### §8 待拍板看板 v3.1(0906 快照)

| ID | 阻塞项 | 持续日数 | 决策影响 |
|---|---|---|---|
| **B1** | Schema 偏离(主计划 §4.3 五表 vs 实际 entity 四表) | 14 日(0824→0906) | 决定 Phase 0.2 批量入库 SQL 模板 |
| **B2** | Phase 0.2 批量入库启动(31 省会 + 重点旅游城市) | 13 日(等 B1) | 决定 Phase 0.2 入库脚本启动日 |
| **B3** | Web App 启动时点(Phase 0.5/1) | 13 日(0825→0906) | 决定 Phase 1 启动周次 + FastAPI 引入时点 |
| **B4** | 0831 承诺 weekly 切换(0831→0906 第 6 日) | 6 日 | **距 0907 周一切换日仅差 1 日,0906 23:59 硬截止线** |

### T1 决策点累计(4 项未动作)

1. **B4 weekly 切换**(0831 承诺,**紧急度本次巡检顶峰**,0906 23:59 硬截止)
2. **untracked `地理顾问开发架构与计划.md` 入库方式**(0902 起草,第 4 日)
3. **B1 Schema A/B/C 决策**(0824 起,第 14 日)
4. **B2 / B3 启动时点**(0825 起,第 13 日)

### 工作区 dirty

- modified:**0** 个(0902 T4 commit `5260525` + `ca2352b` 闭环 dirty 后,0903→0906 无新 commit)
- untracked:**1** 个(`地理顾问开发架构与计划.md` 0902 04:25 起草,19425 bytes / 540 行,等 T1 决定入库方式)
- 24h commit 数:**0**(0905 巡检 `28d6ac4` 之后 24h 无新 commit)
- 静默时长:**72h**(0903 巡检 `05bab80` 之后 72h 无 T4 commit,本次 T4 自举破静默)

### 巡检节奏

- 当前模式:**daily**(每日 02:50 cron)
- 0831 承诺:**weekly**(每周一 02:50 cron)
- 距 0907 硬截止:**1 日**
- 切换命令(待 T1 执行):`mavis cron update <cron_id> --schedule "0 2 * * 1"`

---

> 维护规则:T4 不消费本段(只搬运巡检事实);T1 拍板后由 T4 同步更新本段或交班给下一任 T4
