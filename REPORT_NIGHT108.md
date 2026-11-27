# REPORT_NIGHT108 — 合并夜：N106＋N107 进 master（AutoClaw・单会话）

- 日期：2026-11-27
- 任务：把 night106-mech-design（报告-only 機構設計夜・1f0ac2a＋f3c0779）与 night107-item4-impl（項 4 実施夜・acfa938＋4b73d8f）依次 `git merge --no-ff` 入 master；本地提交、不推远程。
- 结果：**全部验收通过**。合并链＝304ebe2（开工心跳）→ bcb5cc7（合并 106）→ 939598a（合并 107）→ 20fb82d（登记）→ 本提交（wrap-up・提交链见 §6）。

## §1 开工核验

- HEAD＝**f5e0bf3**（N105 wrap-up）✓；pytest **484 passed**（26.13s）✓；已跟踪文件零改动 ✓（untracked 仅历史遗留 eval/ 缓存・ocr_samples 等）
- 两分支 tip 与 merge-base：night106-mech-design＝f3c0779（链 f3c0779←1f0ac2a←f5e0bf3）・night107-item4-impl＝4b73d8f（链 4b73d8f←acfa938←f5e0bf3）・merge-base 均为 f5e0bf3 ✓（任务书「rev-parse＝主提交」为记法偏差・tip＝wrap-up・实质一致）
- origin/master＝f5e0bf3 未变；core.autocrlf=true／safecrlf 未设
- 移交阅读：REPORT_NIGHT106 §3（項 4 实施建议）＋REPORT_NIGHT107 §0（項 4 已实施・审计已清）＝**无 step 0**

## §2 合并（字节安全并集・夜序 106＜107＜108）

- **合并 106＝bcb5cc7**（父 304ebe2＋f3c0779）：冲突恰 **1 处**（SHIFT_LOG）。SHIFT_LOG base 153,659＋N106 段 1,158＋N108 心跳 321＝**155,138 B LF**（wc 156,188 CRLF）。ACCEPT_LOG/ROADMAP master 侧零改动＝自动合流。pytest **484 passed**。
- **合并 107＝939598a**（父 bcb5cc7＋4b73d8f）：冲突恰 **3 处**（SHIFT_LOG/ACCEPT_LOG/ROADMAP）。SHIFT_LOG base 153,659＋N106 1,158＋**N107 2,627（theirs 插中间）**＋接缝 1＋N108 心跳 321＝**157,766 B LF**（ours 差分 1,479＝N106 段＋心跳逐字节相等断言后拆分重组＝N105 坑位③ 同型）；ACCEPT_LOG 12,366＋85（N106）＋170（N107）＝**12,621 B LF**；ROADMAP 51,403＋1,551（N106）＋1,999（N107）＝**54,953 B LF**。pytest **491 passed**。
- 每处并集：blob 全 CR-free 实测→canary blob[807]=**63**（0 基）写前后断言→工作副本 CRLF 化 wc[807]=**243** 断言→`git add` 后**暂存 blob 与 union 逐字节等价**断言→`git commit --no-edit`。
- 接缝字节：N107 分支 SHIFT_LOG blob 末行无终止符（wrap-up amend 遗留）→ N107 段与 N108 心跳之间补 1 B `\n`，两侧内容逐字节原样。
- 防回滚 grep：README 491/13.460/13.466・verify 归档源 night107・accept_night 107 条目・kundoku_rules guard 元组 2 处——全部 N107 版原样在位；106 从未碰过它们。

## §3 验证（最终校验只对 night107 归档）

| 门 | 结果 |
|---|---|
| pytest tests -q | **491 passed**（484→484→491・合并 106 零产品代码実証＋N107 7 条测试生效） |
| golden_4000（tools/night108_eval_4000.py・TestClient 全量 116s） | **13.460／24／0**・与 night107_results_4000.json **全行逐位一致**（diff 0 行・changed_ids_vs_n107=[]）・对照 night104 归档亦 diff 0 行 |
| golden_8165（tools/night108_eval_8165.py・TestClient 全量） | **13.466／30／0**・与 night107_results_8165.json **全行逐位一致**（diff 0 行）・对照 night104 归档 **diff 恰 2 行＝N107 的两行**（rikutou37-2 **44→43**・shiki050-4 **25→20**・fresh 実測）＝「改写 2 行＝N107 的两行」実証 |
| tools/verify_readme_facts.py | **25/25 exit 0**（N107 版・合并后＋README header 补丁后各跑一次） |
| 词库 | **1531**（GLOSSARY_LEXICON 500／_OLD_SIZE 209・extra as_dicts 291・LEXICON_EXTRA2 1031＝_ORDERED_ALL 1531）不动 |

eval 工具＝tools/night108_eval_{4000,8165}.py（night107 型程序化克隆・**assert-only 不写任何归档**＝归档源维持 night107・基线换 night107_results_*.json・8165 版加装「vs night104 diff 恰 2 行」门）。

## §4 登记＋验收

- tools/accept_night.py：NIGHT_ARTIFACTS 照例只加 **108: ["night107_results_4000.json"]** 一条（**106 不登记**＝报告-only 机制・N91/N101/N105 先例；归档源维持 night107）。
- README.md：仅 header 行同步——「数字（2026-11-27 時点、master（Night 108 合并夜：…1f0ac2a＋f3c0779…acfa938＋4b73d8f…合并提交 bcb5cc7→939598a・分支起点 f5e0bf3）…）」（header 指向合并链、自己参照不可＝N104 坑位③・verify 不校验 header）；数字行 491/13.460/13.466 已随 N107 在位・一字未动。
- accept 108 **试跑＝FAIL fail=1（仅 repo_clean・accept_night.py＋README 未提交 2 文件）＝设计行为**（N96/N100/N104/N107 先例）；**登记提交 20fb82d 后终跑＝PASS fail=0 skip=0（33.1s）**（七门全绿・pytest 491=491・eval_integrity 查 night107_results_4000.json）；FAIL/PASS 两行とも ACCEPT_LOG 留存。

## §5 本夜不碰清单（自查）

backend/ 产品代码（guard 元组 2 处为 N107 分支内容原样带入）・tests/・golden expected・词库三模块・verify_readme_facts.py・既有規則 repl/链序/長词表・night106/night107 两分支本体（原样合入・不重做不改数）・C2（無/罔字拡張）C8（tail→全文機構）禁实施遵守・項 3/5/6/7/8/9 与 (c) 后继字機構原样带入未動。禁 OCR・禁 guwenbert・禁 eval 以外的网络（本夜零网络）。

## §6 提交链与远程状态

```
304ebe2  Night 108 开工心跳（SHIFT_LOG＋1 行・merge 前落位＝N100 坑位①）
bcb5cc7  Merge branch 'night106-mech-design'      （冲突 1・SHIFT_LOG 并集）
939598a  Merge branch 'night107-item4-impl'       （冲突 3・三日志并集）
20fb82d  Night 108 登记（NIGHT_ARTIFACTS 108・README header・REPORT_MERGE_106_107・night108 eval 工具・ACCEPT_LOG FAIL 行）
本提交   Night 108 wrap-up（REPORT_NIGHT108・ACCEPT_LOG PASS 行・accept_night_108.json 终跑版）
```

未合他处・未推远程；rev-list 超前 origin/master＝本夜 5 提交＋两分支 4 提交＝9（等用户手推）。

## §7 记录偏差与坑位

1. 任务书「rev-parse＝主提交」记法偏差（tip＝wrap-up）——实质一致，REPORT_MERGE_106_107 §1 注记 A。
2. N107 分支 SHIFT_LOG blob 末行无终止符→并集接缝 1 B（REPORT_MERGE_106_107 §3.1 注记 B）；合并 106/107 各段 ours/theirs 差分均以「与已落盘段字节逐字节相等」断言保护，不靠文本标记搜索。
3. SHIFT_LOG 非纯 UTF-8（byte[807]=0xf3）＝并集全程纯字节操作；canary 0 基索引 blob[807]=63／CRLF[807]=243 写前后实测断言（N105/N106 教训再确认）。
4. 开工时工作区签出在 night107-item4-impl（N107 收工状态）——先 checkout master 再做正式开工核验（N106/N107 报告的「master 核验」均在其各自分支上下文中，本夜为合并夜必须以 master 为基）。
5. 心跳生成文用 ASCII＋ISO 时间戳（N106 风格）＝U+7232 字形混淆坑位规避；报告/提交消息同样不含该字形。
6. accept 试跑 FAIL=repo_clean 1 项＝设计行为・两行留存（N96/N100/N104/N107 先例再确认）。

## §8 次夜建议

- 等用户手推 origin/master（本夜 9 提交待推）。
- 在庫棚卸し／拍板表更新夜：項 5 は系「放弃」記載更新（N106 §2.2 负结果）・項 7 嗟や・項 6/8 毋系在庫（Δ−0.000490／−0.000367）・項 9 剥夹注管线・N84 残渣 2 行・echo 30 行。
- (c) 守り字后继字機構改设计 probe（got 側文末・係り結び系 2 次判別・报告-only・収益 −0.0023〜−0.0027・rikutou26-5 変差 1 行拍板許容別途）。
- NIGHT_ARTIFACTS[108]=night107_results_4000.json（归档源 night107 维持）。
