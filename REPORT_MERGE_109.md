# REPORT_MERGE_109 — Night 110 合并夜：night109-inventory 一括 --no-ff 入 master

Night 110（合并夜）＝把 night109-inventory（在庫盘点＋拍板表更新夜・報告-only・2 提交
0945e45 主＋bf50046 wrap-up）一次 `--no-ff` 合入 master。合并＝产品代码零改动（N109 是
報告-only 夜・backend/词库/golden/README/verify/tests/accept_night 一字未改），所以合并后
真跑出力＝night107 归档全行逐位一致（4000 13.460/24/0・8165 13.466/30/0）。

## §1 开工核验（合并前）

- `cd D:\kanbun-kakikudashi`・先 `git checkout master`（上夜收工时签出在 night109-inventory＝N108 坑位②）✓
- HEAD＝**141a9bf**（N108 wrap-up）✓・`pytest tests -q`＝**491 passed**（14.6s）✓・已跟踪文件零改动 ✓
- 分支核验：`git rev-parse night109-inventory`＝**bf50046**（tip＝wrap-up 提交・任务书已按正确写法），
  其父＝**0945e45**（主提交）✓・`git merge-base master night109-inventory`＝**141a9bf** ✓
- origin/master＝141a9bf（用户已推 N108 链・status 显示 up to date）✓
- 防回滚 grep（README/verify/accept_night 以现 master＝N107 版为准・109 从未碰过）：
  `tools/verify_readme_facts.py` 归档源＝**night107**（eval/night107_results_4000.json）✓・
  README 有 **13.460／13.466／491** ✓・accept_night.py 有 **107 条目**（＋108 条目・同指 night107_results_4000.json）✓
- 先读 REPORT_NIGHT109 §0/§3（git show night109-inventory:REPORT_NIGHT109.md）：在庫 5 項数値漂移 0・
  記録偏差 1（N102 §5 行 94 行名転記错位→実測 rikutou21-2・koshi19_01-8）・新版拍板表＝§3 supersede
  N98 §3（表の更新のみで実施は一切しない）・审计已清无 step 0

## §2 合并（一次 --no-ff）

- 开工心跳提交 **e0a86d3**（master 上先落一行心跳・防空合并・N100 坑位①）：SHIFT_LOG +1 行
  （d_ours＝251 B LF・ASCII・canary blob[807]=63／CRLF[807]=243 写前后实测・staged blob＝base+d_ours 逐字节断言 ✓）
- `git merge --no-ff night109-inventory` → **冲突恰 1 处**＝SHIFT_LOG.md（UU・追加-追加）。
  ACCEPT_LOG.md／ROADMAP.md＝ours 侧零改动→git 自動合流（staged blob＝theirs blob 逐字节断言通过）。
  新文件 9 个自动带入（REPORT_NIGHT109.md・tools/night109_sim.py・tools/night109_status.py・
  eval/night109_{sim.json,sim.txt,changed_rows.json,status.json,status.txt}・eval/accept_night_109.json）
- SHIFT_LOG 字节安全并集（纯字节操作・禁整文件 decode・禁文本三路合并）：
  base（141a9bf）＝157,766 B・theirs blob（bf50046）＝158,195 B（d_theirs＝**429 B**＝N109 心跳 2 行・
  末尾 LF 有→**接缝 0 B**（N108 注记 B 同型检查实施））・ours blob（e0a86d3）＝158,017 B
  （d_ours＝**251 B**＝N110 开工心跳 1 行）→ **union＝theirs blob＋d_ours＝158,446 B**
  （夜序 **109＜110**＝N109 心跳 2 行在前・N110 心跳在末尾・末尾 3 行目视确认）。
  暂存 blob＝union 逐字节等价断言 ✓・无冲突标记 ✓
- canary（0 基索引・N105 教训）：并集后 **blob[807]=63／CRLF 工作副本[807]=243** 写前后实测 ✓
  （SHIFT_LOG 非纯 UTF-8 历史区域 byte[807]=0xF3・全程纯字节操作）
- SHIFT_LOG 行数账：blob LF **1,058 行**（base 1,055＋N109 心跳 2＋N110 心跳 1）＝工作副本 CRLF 159,504 B ✓
- 合并提交＝**7b7951e**（父 e0a86d3＋bf50046・--no-ff）

## §3 字节账（三日志）

| 文件 | base(141a9bf) | theirs(bf50046) | d_theirs | ours(e0a86d3) | d_ours | 合并结果 blob | 断言 |
|---|---|---|---|---|---|---|---|
| SHIFT_LOG.md | 157,766 B（1,055 行） | 158,195 B | +429 B（N109 心跳 2 行） | 158,017 B | +251 B（N110 心跳 1 行） | **158,446 B**（1,058 行・CRLF 159,504 B） | staged=union・夜序 109<110・接缝 0 B・canary 63/243 |
| ACCEPT_LOG.md | 12,791 B | 12,961 B | +170 B（accept 109 FAIL/PASS 两行） | =base | 0 | 12,961 B | staged=theirs blob 逐字节 ✓ |
| ROADMAP.md | 54,953 B（142 行） | 57,558 B | +2,605 B（Night 109 行 1 行） | =base | 0 | 57,558 B（143 行） | staged=theirs blob 逐字节 ✓ |

合并夜自身不加 ROADMAP 行（N108 先例＝合并夜不加自行・Night 109 行由 N109 分支带入）。

## §4 验证（最终校验只对 night107 归档）

- `pytest tests -q`＝**491 passed**（15.1s・合并后）
- golden_4000 全量真跑（tools/night110_eval_4000.py・assert-only 不写归档・night108 型程序化克隆）：
  **13.460／24／0**＝night107_results_4000.json **全行逐位一致（diff 0 行・changed_ids_vs_n107=[]）**・
  对照 night104 归档 diff 0 行（両改写行 rikutou37-2/shiki050-4 4000 外）
- golden_8165 全量真跑（tools/night110_eval_8165.py）：**13.466／30／0**＝night107_results_8165.json
  **全行逐位一致（diff 0 行）**・对照 night104 归档 diff **恰 2 行**（rikutou37-2 44→43・shiki050-4 25→20
  ＝N107 的两行・fresh 実測 d 值一致）＝合并零改动実証
- 词库 **1531**（500＋209＋291・_ORDERED_ALL 1531）不动 ✓
- `tools/verify_readme_facts.py`＝**25/25 exit 0** ✓
- README header（登记提交内更新）：Night 108 合并链→**Night 109 合并链（合并提交 7b7951e・分支起点
  141a9bf・自己参照不可＝N104 坑位③・verify 不校验 header）**・数字行 491／13.460／13.466 不变（N109 零产品代码）

## §5 坑位与注记

- 注记 A（行数断言笔误）：并集脚本 CRLF 行数断言初写 1,057（誤算）→実測 **1,058**（base 1,055＋2＋1）
  ＝断言在写盘前失败无实害・修正后重跑全绿——「canary 先实测再写数」的行数版。
- 注记 B：theirs blob 末行终止符检查＝d_theirs 末尾 LF 有（**接缝 0 B**・N108 注记 B 同型・本次无需补）。
- 注记 C：night110 eval 工具＝night108 型程序化克隆（token 替换带出现次数断言＋陈旧 token grep
  ＋ast 检查＝N101 坑位①三连・工具内不写归档）・断言结构与 night108 版相同（vs night107 diff 0・vs night104 对照）。
- 注记 D：8165 eval 第一次运行の产物 stdout 被 capture 截断（stderr INFO 洪水挤占）→exit 0（FAIL 路径 exit 2）
  ＋stderr 丢弃重跑完整判定行取得——长跑工具の判定确认は stderr を丢弃して再取得が確実。

## §6 提交链（本夜）

- e0a86d3（开工心跳）→ 7b7951e（Merge branch 'night109-inventory'・--no-ff）→ 登记提交（＝本提交：
  NIGHT_ARTIFACTS 加 110＋README header＋本报告＋tools/night110_eval_4000/8165＋ACCEPT_LOG 试跑行）→
  wrap-up（REPORT_NIGHT110＋ACCEPT_LOG 终跑行）＝本夜 4 提交・不合他处・未推远程（等用户手推・
  rev-list 超前 origin＝4）。
