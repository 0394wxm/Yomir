# REPORT_NIGHT60

## 0. 一句话结论

评测扩到 **4000 条**：`eval/golden_4000.json` 建成（前 3000 条与 golden_3000
**逐条相等且顺序一致**——构建断言 + pytest 双保险；新增 1000 条全部来自
kanbun.info /syubu/ 剩余栏目补抓（night57 抓取器凑满 1100 对即停、歴代/唐詩選
内容页从未访问过的部分），expected 一字不改、**0 重复**）；规则引擎全跑
**avgDist 13.889、精确 19/3998**（前 3000 条 vs night58 归档 **diff = 0**，
跨夜跨进程确定性对照第四次成立）；**新增段又出一条 應(必要) KeyError
（toushisen043-16）——N59 拍板⑬ 的「非孤例」论据被扩语料直接证实**；
guwenbert 新增段 **6.639** vs 规则 **6.896**，逐条 **规则 291 / guwenbert 373 /
持平 335**（guwenbert 略优但差距 0.257，与 N57 五五开同型）。pytest **190→193**。

## 1. 来源盘点与补抓（`tools/night60_scrape_left.py` → eval/night60_scraped_left.json）

- N57 抓取器 TARGET_PAIRS=1100，凑满即停：196 页 1101 对全部是 shikyo(102)+shijin(999)，
  **歴代/唐詩選内容页一个都没访问**；shijin 索引本身有大量未抓内容页；
- 本夜补抓：shijin 剩页 → toushisen000 索引 → reki_* 索引（去重已抓/已入 golden 的
  196 页），解析与 N57 完全同款（genbun01 + yomi02/03；剥 ruby/标签+去空白；
  expected 一字不改；限速 0.4s + 重试 3）；
- 实际抓 **184 页 / 1203 对 / 471s**（缓冲 1200 达标即停；shijin 索引本身就链到
  唐詩選内容页如 toushisen388+，来源标签按入口索引记，全部 /syubu/ 文本对）；
- 对 golden_3000 hakubun 去重后 0 重复跳过——抓的就是纯新增。

## 2. golden_4000（`tools/night60_build_golden_4000.py`）

```
total 4000 | uniq ids 4000 | uniq hakubun 3975（base 25 条内部重复原样保留）
新增 1000 = /syubu/ 补抓 1000（skipped {} —— 0 重复）
新增分档: ≤20字 1000            ← 又全是诗短句，构成注意（N56 教训第三次适用）
新增文体: 漢詩 1000
```
- 硬断言：`combined[:3000]` 与 golden_3000 逐条 dict 相等且顺序一致（构建时 +
  `tests/test_golden_4000.py` 双保险）；
- 文体全景：故事 1333 / 論語 362 / 大学 189 / 孝経 147 / 詩経 102 / **漢詩 1867**；
- 分档：≤20字 3043 / 21-40字 542 / 41-60字 247 / >60字 168。

## 3. 规则引擎全跑（`tools/night60_eval_4000.py`，132 秒，D/E/F/G/H 全链 + SHINJITAI 30 对）

```
engine OK 3998 / error 2 | 精确 19/3998 | avgDist 13.889
分档  ≤20字 7.840(3041)  21-40字 21.742(542)  41-60字 37.162(247)  >60字 63.845(168)
文体  漢詩 6.990  故事 21.096  論語 26.870  大学 14.571  孝経 9.286  詩経 5.167
```
- **确定性对照（本夜最强证据）**：前 3000 条重跑输出 vs night58 真机归档
  **输出文本不同行数 = 0**（引擎确定性 + 规则未变，跨夜跨进程第四卷：D17 §6、
  N55 §8、N57 §4 之后，且 N58 是 317/317 逐位一致）；
- **整体 13.889 < 3000 条的 16.219 是构成效应**（新增段 100% ≤20 字短诗拉低平均），
  不能读成「引擎变好」——分档数字前 4 档与 N58 完全一致（7.840 vs 8.302 的
  ≤20字变化全部来自新增段短句混入）；
- **error 2 条**（N57/58 时 1 条）：
  - `toushisen135-12`「應知黃綺心」——N59 定性的 AUX 缺應(必要) 条目；
  - `toushisen043-16`「應照離人粧鏡臺」（expected「応に照らすべし　離人の粧鏡臺」）
    ——**同类 KeyError，N59 §6 的「非孤例、用户输入类失败」论据被扩语料直接证实**
    （拍板⑬ 的证据强度从 1 例变 2 例，且都是唐詩選高频词「応に」句式）；
    **guwenbert 路径同一行同一 KeyError**（kundoku 翻译层共享，N57 同型发现）——
    AUX 缺口断的是两条引擎路径。

## 4. guwenbert 新增段（`tools/night60_guwenbert_new.py`，离线，864 秒推理 + 100s 建引擎）

```
guwenbert 999 OK / error 1（toushisen043-16，應 KeyError 同规则侧） | 精确 1/999 | avgDist 6.639
规则（同 999 条）            | 精确 3/999 | avgDist 6.896
逐条对决：规则更好 291 | guwenbert 更好 373 | 持平 335   ← guwenbert 略优
```
- 与 N57（规则 7.122 vs gwb 7.075，306/325/368 五五开）对比：本批 guwenbert 领先
  扩大到 0.257（3.7%）——与前两批「平均差 <0.05」不同型但仍是同一量级，
  逐条双方各有大量胜负（规则相对优势 top：可憐春半不還家 9vs17；gwb 相对优势
  top：盧家少婦鬱金堂 8vs1）。「要不要接 guwenbert」仍是 D16 时留的产品拍板，
  本夜数据方向上略微有利于 guwenbert 但不改变拍板结构。

## 5. 本夜改动清单

| 文件 | 性质 |
| --- | --- |
| `eval/golden_4000.json` / `golden_4000_stats.json` | 新评测集（前 3000 字节级保留） |
| `tools/night60_scrape_left.py` / `night60_build_golden_4000.py` / `night60_eval_4000.py` / `night60_guwenbert_new.py` / `night60_h2h.py` / `night60_error_row.py` | 抓取/建库/评测/对照 |
| `tests/test_golden_4000.py` | +3 条完整性测试 |
| `eval/night60_scraped_left.json` / `night60_results_4000.json` / `night60_guwenbert_new1000.json` / `*.txt` | 证据 |
| `REPORT_NIGHT60.md` / `SHIFT_LOG.md` | 报告与夜志 |

## 6. 验证汇总

- pytest **190 → 193 passed**（+3 test_golden_4000）；
- `python tools/accept_night.py 60`（见 eval/accept_night_60.json）；
- GT CER：本夜**零 backend 代码改动**（只有 eval 数据与 tools 评测脚本），
  N58 当夜 GT 实测（raw 0.3568 / norm 0.3053 逐位不变、night49 归档 sha256
  `ff21e4fa…`）直接覆盖；
- expected 一字不改：抓取器与 N57/D16 同款「剥 ruby/标签+去空白」，golden_3000
  前缀由构建断言 + pytest 双重锁定。

## 7. 待拍板（编号 = 下一班的下单清单）

1. N52-59 的全部既有拍板项原样保留（⑩ 已有 N59 否决建议待确认、⑬ 待拍板）；
2. **新增 ⑭**：golden_4000 要不要登记进 `accept_night.py` 的 `NIGHT_ARTIFACTS`
   （同 N57 ⑨：需先统一 list 形状），以及 4000 条要不要成为新的默认评测口径
   （对比基准从 night57 系列切到 night60 系列）；
3. **新增 ⑮**：/syubu/ 抓取还剩 ~270 页未访问（shijin 尾部 + reki_* 内容页 +
   toushisen 索引尾部，本次 1203 对即停）——要不要继续扩到 5000（预计还能出
   ~1000 对短诗），以及是否开始担心「评测集偏科」（4000 条里 漢詩 1867 条全是
   ≤20 字短句，長句档的增量空间只剩 歴代里的散文/赋类页面）。

## 8. 禁止事项自查

未发图/未读图/未抄 GT ✓；未改 `eval/ocr_gt_100.tsv`、`eval/golden*.json`
（golden_3000 原样、只**新增** golden_4000）✓；未重跑 47 页全本 OCR ✓；
未碰 Night 9、16-20 ✓；未动 N51-59 拍板项 ✓（⑬ 的 AUX 补丁未打——只诊断红线
延续到证据面）✓；expected 一字未改 ✓；本地提交不推远程 ✓；心跳按小时追加 ✓。

## 9. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\night60_scrape_left.py       :: 补抓剩余栏目 → eval/night60_scraped_left.json
python -I tools\night60_build_golden_4000.py :: 建库（前缀硬断言）
python -m pytest tests -q                    :: 193 passed
python -I tools\night60_eval_4000.py         :: 规则引擎 4000 条 + 确定性对照
python -I tools\night60_guwenbert_new.py     :: guwenbert 新增段（离线，~19min）
python -I tools\night60_h2h.py               :: 逐条对决
python tools\accept_night.py 60              :: 验收门
```
