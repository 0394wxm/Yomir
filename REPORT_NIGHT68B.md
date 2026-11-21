# REPORT_NIGHT68B

## 0. 一句话结论

Night 68 审计发现的 README 漂移三处（正字化 246 組、已知问题① 24/3998＋分档、表头/統合状況
54d2410）全部修补，verify_readme_facts.py 从「只打印」升级为「逐项 grep 比对」（13/13 对上，
FAIL 即 exit 1），NIGHT_ARTIFACTS[68] 补登记后 **accept 68 重跑 PASS（fail=0 skip=0，
eval_integrity skip→实查）**。構成节 pytest 214 经现场核验已在 Night 68 主提交改毕（审计口径滞后）。
规则/后端/评测数据零改动，本地 master 两提交（02b0298＋wrap-up），未推远程。

## 1. 开工核验

- `git log -1` = `9fca166`（= Night 68 wrap-up，ahead 2 未推）✓；tracked 零改动 ✓
- `pytest tests -q` = **241 passed** ✓；SHIFT_LOG 开工心跳 byte807=**243** ✓
- REPORT_NIGHT68.md §6/§7 已读：§6 宣称「README 数字行同步」处即本夜修补对象

## 2. README 修补（git show HEAD:README.md 现场取数，逐项 grep 复核）

| # | 行 | 改前值 | 改后值 | 取数来源 |
|---|---|---|---|---|
| 1 | 正字化行（L22） | `SHINJITAI_MAP 旧字体→新字体 **246 組**（N64 で 99 組を追加…）` | `**275 組**（N64 で 99 組追加、N68 で 29 組追加——総数は backend/kundoku_rules.py の len 実測…）` | `len(SHINJITAI_MAP)` 实测 = 275（verify 输出首行） |
| 2 | 已知问题①（L146） | `24/3998`、`（3041 条、平均編集距離 7.74）`、`漢詩 6.903／詩経 5.157 …故事 20.861／論語 26.472（N64 マージ後の口径）` | `24/4000（N68 口径 eval/night68_results_4000.json、error 0）`、`（3043 条、7.73）`、`漢詩 6.896／詩経 5.157 …故事 20.790／論語 26.436（N68 口径）` | night68_results_4000.json summary（exact 24 / avg 13.684；by_bucket ≤20字 n=3043 avg 7.728；by_genre 见下） |
| 3 | 数字节表头（L14） | `master 54d2410 のコード／アーカイブから実測` | `master 9fca166 の…` | 开工 HEAD（git log -1） |
| 4 | ブランチ統合状況（L37） | `最終 HEAD が 54d2410` | `最終 HEAD が 9fca166` | 同上（任务书指定两处 54d2410 → 9fca166） |

**分档数逐项对 night68 归档核对（known-issues 分档）：漢詩 6.903→6.896（改）、詩経 5.157（未变）、
故事 20.861→20.790（改）、論語 26.472→26.436（改）——3 改 / 1 未变**（`by_genre`：
漢詩 1867 条 6.896／詩経 102 条 5.157／故事 1333 条 20.790／論語 362 条 26.436）。

**構成节（tests/ pytest 214 条）现场核验**：L92（`# テスト（241 条）`）与 L162（`tests/ pytest 241 条`）
均已为 241——Night 68 主提交 d5629e8 已改在位，审计「構成 214 未改」口径滞后，**无漂移、68B 零改动**。

**其余数字行**：verify 比对段 13 项全 OK（golden_4000 4000 組/uniq 3975、golden_7908 7908 組、
MERGE_WORDS 21 語、OCR GT 92 行、CER 0.3568/0.3053、右先率 98.57%/98.63%/296 対/100%、
規則エンジン 13.684/24/4000、Rule J 7 語、テスト 241）——无一漂移，逐项证据见 §3。

## 3. verify_readme_facts.py 比对段（print-only → 逐项 assert）

原脚本只打印数值不比对 README 文本，按任务书加比对段（其余不动）：13 项 grep 断言
（空白规整后包含判定），任一 FAIL 打印漂移项并 `sys.exit(1)`。实跑输出（exit 0）：

```
SHINJITAI_MAP: 275 对 | MERGE_WORDS: 21 条 | Rule E/F/G/H/I/J: 5/4/4/3/6/7
night68(golden_4000): total=4000 n=4000 exact=24 avgDist=13.684 errors=0
golden_4000: total=4000 uniq_hakubun=3975 | golden_7908: total=7908 uniq_hakubun=7883
ocr_gt_100.tsv: 93 行（GT 92 行＋表头 1 行） | 割注右先率基线: off=98.57% on=98.63% strict=100.0%
README 比对 SHINJITAI 組数      OK（**275 組**）        README 比对 OCR CER raw     OK（**0.3568**）
README 比对 MERGE_WORDS 語数    OK（**21 語**）         README 比对 OCR CER norm    OK（**0.3053**）
README 比对 avgDist             OK（**13.684**）        README 比对 右先率 off/on   OK（98.57% / 98.63%）
README 比对 exact               OK（**24/4000**）       README 比对 严格層対数      OK（296 対）
README 比对 golden_4000 組数    OK（**4000 組**）       README 比对 Rule J 語数     OK（**7 語**）
README 比对 golden_4000 unique  OK（3975）              README 比对 golden_7908     OK（**7908 組**）
README 比对 OCR GT 行数         OK（**92 行**）
README 比对: 13/13 对上   exit=0
```

## 4. 验收门补登记＋重跑（③）

- tools/accept_night.py `NIGHT_ARTIFACTS` 照 67 号登记式加一行：
  `68: ["night68_results_4000.json"],`（67 号同行 `67: ["night67_results_4000.json"],` 紧邻其上；
  68 号实跑产物含 4000/8165 两口径，登记 4000 口径那份，与 67 号同制）
- `python tools/accept_night.py 68` 重跑：**verdict: PASS（fail=0 skip=0，29.1s）**
  ——`eval_integrity` 由 skip 转实查并 PASS（评测归档完整、id 唯一、expected 未被改）；
  `repo_clean` PASS、`pytest` PASS（241=241）、`rule_regression`／`engine_smoke`／`perf_envelope` PASS、
  `order_rate` off 98.57%（+0.00pp）／on 98.63%（+0.00pp）、严格层 296/296＝100%、退化页 0
- Night 68 首跑 skip=1 的缺口就此闭合（ACCEPT_LOG 本次重跑 PASS 行在案）

## 5. REPORT_NIGHT68.md 三处失实勘误（N68 报告不改写，勘误仅在此）

1. **正字化 246 未改——失实成立**。REPORT_NIGHT68.md §6 宣称 README 数字行已同步，但漏了
   正字化行（`246 組` 遗留，N68 只改了テスト/規則エンジン/ルールチェーン/構成注释等行）；
   68B 已修 246→275 組（§2 第 1 项）。
2. **構成 214 未改——经现场核验不成立（审计口径滞后）**。README L92/L162 在 Night 68 主提交
   d5629e8 中已改 241（`git show d5629e8:README.md` 可证），68B 现场复核无漂移、零改动；
   审计的「構成 214 未改」与文件实值不符，如实勘误在此。
3. **表头 920866d 与文件实值 54d2410 不符——失实成立（源出 Night 67 报告）**。
   REPORT_NIGHT67.md L129 声明「表头 commit 号维持开工 HEAD 920866d」，而 README 文件实值
   两处均为 54d2410（N65/66 同步时的旧值）——该漂移遗留到 68 审计被抓；68B 已将两处改至
   开工 HEAD 9fca166（§2 第 3/4 项）。**自引用滞后如实记录**：本报告对应的主提交 02b0298
   落盘后 HEAD 已再变，表头按任务书只指向 9fca166，不为它多跑一轮。

## 6. 禁止事项自查

- 只动允许清单内文件：README.md（数字行）、tools/accept_night.py（仅 NIGHT_ARTIFACTS 一行）、
  tools/verify_readme_facts.py（仅加比对段）、ROADMAP.md（末尾一行）、SHIFT_LOG.md、
  ACCEPT_LOG.md（accept 重跑自动追加）、eval/accept_night_68.json（重跑产物）、REPORT_NIGHT68B.md
  ——规则/backend/评测数据零改动 ✓；REPORT_NIGHT68.md 未改写 ✓
- golden expected 未动（accept eval_integrity 实查 PASS 佐证）✓；site-packages 未动 ✓
- SHIFT_LOG byte807=243 ✓；本地 master 两提交（02b0298＋wrap-up），**未推远程** ✓
