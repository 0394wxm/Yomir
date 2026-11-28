# REPORT_NIGHT114 — 合并夜：night113-inventory → master（ZCode 单会话）

## 0. 结论（先说）

**Night 114 完成：night113-inventory（N113 在庫盘点＋拍板表更新夜・報告-only・306898f＋fa71e23）を一次 --no-ff（merge 提交 59ca4cd）で master に合流・全部验收通过。** 冲突恰 1 处（SHIFT_LOG.md）字节安全并集（161453+385+285+0=162123 B・夜序 113<114・接缝 0・canary 双形态実測・哨兵守恒）＝**REPORT_MERGE_113.md 参照**。验证＝pytest **503 passed**（0 新增）・golden_4000 **13.455／24／0**・golden_8165 **13.464／30／0**（ともに night111 归档全行逐位一致 diff 0 行＝产品代码零改动実証）・verify **26/26 exit 0**・词库 **1531 不动**。accept 114 ＝试跑 FAIL（repo_clean 1 項設計行為）→ 终跑 **PASS fail=0 skip=0**（37.5s・七门全绿・order_rate 98.57/98.63 不変）。拍板表は N113 §3 更新済み＝**本合并夜不改**（REPORT_NIGHT113.md §3 参照）。本夜 4 提交（心跳 a73989e／merge 59ca4cd／登记 cb4270d／wrap-up＝本提交）＋合并带入 N113 两提交＝**rev-list 超前 origin 6**・未推远程（等用户手推）。

## §1 开工核验

- `cd D:\kanbun-kakikudashi`・`git checkout master` ✓・HEAD＝**ed5b2db**（N112 wrap-up）✓・origin/master＝ed5b2db（rev-list 超前 **0**＝用户已推 N112 链実測）✓・已跟踪零改动 ✓・git 身份 wang／wang@localhost ✓
- pytest tests -q 两侧＝**503 passed**（master 22.01s・分支 20.25s・ともに exit 0＝N113 未改产品代码・0 新增测试）
- 分支核验：night113-inventory tip＝**fa71e23**（wrap-up）・其父＝**306898f**（主提交）・merge-base＝**ed5b2db** ✓・分支 diffstat 12 文件 +4406/−0＝報告-only 触碰範囲と任務書逐項一致
- grep 防回滚（master 版）：verify 归档源＝night111 ✓・README 13.455/13.464/503 ✓・accept_night.py 111/112 条目 ✓
- REPORT_NIGHT113.md §0/§3/§5 読済（§3 新版拍板表＝supersede N98 §3/N109 §3・§5 坑位 6 項＝うち新規 3 項）

## §2 合并（概要）

心跳提交 **a73989e**（17:55）→ `git merge --no-ff night113-inventory` → **冲突恰 1 处 SHIFT_LOG.md（UU）**・ACCEPT_LOG/ROADMAP 自動並入・N113 10 文件干净带入 → tools/night114_merge_log.py で**字节安全并集**（blob 級・纯字节・夜序 113<114・接缝 0・canary LF [800]=243/[807]=63＋CRLF 虚拟 [807]=243・哨兵守恒 N111=8/N112=4/N113=2/N114=1）→ merge 提交 **59ca4cd**（父 a73989e＋fa71e23）。**字节账・冲突清单・canary・坑位の全詳細＝REPORT_MERGE_113.md §2**。

## §3 验证（最终校验只对 night111 归档）

| 项 | 実測 | 期待 |
|---|---|---|
| pytest tests -q（合并後） | **503 passed**（15.60s）exit 0 | 503・0 新增 |
| golden_4000 全量（tools/night114_eval_4000.py・TestClient） | **13.455／24／0**・vs night111 归档 **diff 0 行**・vs night107 恰 N111 発火 12 行・138s exit 0 | 逐位一致 |
| golden_8165 全量（tools/night114_eval_8165.py・TestClient） | **13.464／30／0**・vs night111 归档 **diff 0 行**・vs night107 恰 N111 発火 15 行・約 280s exit 0 | 逐位一致 |
| 词库 | **1531 不动**（core 500＝209+291・extra2 1031・_ordered_entries 1531） | 不动 |
| verify_readme_facts.py | **26/26 exit 0** | 26/26 |

stderr＝httpx INFO 洪水（TestClient 既知）＝exit code 判定＋[OK] 行 grep 确认（N110 坑位）。eval 工具は assert-only＝归档に何も書かない。

## §4 登记＋提交

- **NIGHT_ARTIFACTS** 加 `114: ["night111_results_4000.json"]`（归档源维持 night111・**113 不登记**＝報告-only N98/N102/N103/N106/N109 先例）。
- **README header**：Night 114 合并链 59ca4cd・分支起点 ed5b2db（数字行 13.455/13.464/503 不変＝合并零改动・verify 不校验 header）。**ROADMAP 無改**（合并夜先例 N110/N112＝合并夜は ROADMAP 行を追加しない）。
- **REPORT_MERGE_113.md**（字节账＋冲突清单＋§5 口径交代＋坑位节）＋tools/night114_merge_log.py＋tools/night114_eval_4000/8165.py＝登记提交 **cb4270d**（＋ACCEPT_LOG 試跑 FAIL 行＋SHIFT_LOG 进度心跳）。
- **accept 114**：試跑（提交前）＝**FAIL fail=1 skip=0**・repo_clean 1 項のみ（設計行為・他 6 項全 PASS・39.9s・N96/N100/N104/N107/N109/N113 先例）→ 登记提交後終跑＝**PASS fail=0 skip=0**（37.5s・七门全绿・order_rate off 98.57%／on 98.63% 基線差 +0.00pp 不変）。FAIL/PASS 两行とも ACCEPT_LOG に残す。
- **wrap-up 提交（本提交）**：REPORT_NIGHT114.md＋ACCEPT_LOG.md（FAIL/PASS 两行）＋eval/accept_night_114.json（final PASS）＋SHIFT_LOG.md（收工心跳）。
- 本夜 4 提交（心跳 a73989e／merge 59ca4cd／登记 cb4270d／wrap-up）＋合并带入 N113 两提交（306898f＋fa71e23）＝**rev-list 超前 origin 6**（N110 坑位：计数含分支带入提交）。不合他处・**不推远程**。

## §5 口径交代（任務書必述 3 項・詳細＝REPORT_MERGE_113.md §5）

1. **N113 记录偏差（非漂移）**：N98 §3/N109 §2(e) 例示字形「爲→为」vs 実測／SHINJITAI_MAP「爲→為」（U+7232→U+70BA）＝報告文例示 slip のみ・行集行数 16 行一致・REPORT_NIGHT98/109 自体は歴史記録不変。
2. **拍板表**：N113 §3 で更新済み（supersede N98 §3/N109 §3）＝**本合并夜は拍板表に一切触れない**（表内実施項ゼロ）。
3. **N113 新坑位 3 項**（変体 census delta 口径／sorted(set)==set 恒 False／归档 JSON 保存序非 sorted）＝REPORT_MERGE_113.md §6 に恒久化収録済み。

## §6 坑位（合并夜新知見＝REPORT_MERGE_113.md §6 参照）

1. canary 双值 assert 化（LF blob [800]=243/[807]=63・CRLF 虚拟 [807]=243＝別物理字节）。
2. 工作树サイズ vs blob サイズ（autocrlf=true・CRLF 检出 1067 行＋1067 B）＝実測は全部 blob 級で。
3. 承 N112：merge 前心跳・裸夜号哨兵誤匹配・机械并集夜序逆序（夜号升序直接構造＋位置断言で回避）・rev-list 含带入提交・長跑 exit code 判定。

## §7 禁碰区確認

backend/・词库（1531 實測不動）・golden expected・tests/・tools/verify_readme_facts.py・REPORT_NIGHT98.md・REPORT_NIGHT109.md・REPORT_NIGHT113.md（歴史記録）・night106–113 分支＝**全部未動**（README は header 1 行のみ・accept_night.py は NIGHT_ARTIFACTS 1 条目のみ）。OCR／guwenbert／eval 外网络＝不使用。

## §8 次夜建议（只建议・未开工・全部ユーザー拍板待ち＝N113 §6 引き継ぎ）

1. **剥夹注管線設計**（項 9・detect_text_type 口径改訂＋全量回帰必須＝report-only 設計夜から推奨）
2. **嗟や stock 拍板**（項 7・N113 再測 3/3/0 Δ−0.000367・収録線未達のまま＝収録線撤廃か歎詞データ増強か維持か）
3. **毋系 per-guard 拡張実施拍板**（項 6 在庫残①・N111 4 元組同型の第二 entry・site 4・Δ−0.000490 収録線未達＝単独では在庫・収録線撤廃/複数候補一括時の浮上候補）
