# REPORT_NIGHT57

## 0. 一句话结论

评测扩到 **3000 条**：`eval/golden_3000.json` 建成（前 2000 条与 golden_2000 **逐条
相等且顺序一致**——测试锁死；新增 1000 条全部来自 kanbun.info：平行语料剩余 31 +
**新栏目 /syubu/ 詩経 102 + 漢詩 867**，expected 一字不改，抓取器只做剥 ruby/去空白）；
规则引擎全跑 **avgDist 16.321、精确 15/2999**（1 条 error = 引擎词典缺「應」）；
**Rule G 确定性对照：前 2000 条与 day17 归档差异行数恰为 136**、且前 2000 avgDist
**20.916 与 N55 离线预测逐位一致**（127 改善/0 变差）；guwenbert 新增段
**7.075 vs 规则 7.122**，逐条 **306/325/368 五五开**。pytest **172→175**。

## 1. 来源盘点（为什么必须抓新栏目）

- `eval/kanbun_parallel.json`（Night 28 全站语料 1705 对）在 golden_2000 里**已用尽
  （剩余 0）**——其实它 100% 来自 /koji/ 故事页（1130 页 × 每页 10 对封顶）；
- `day16_pool.json` 剩余仅 **31 条**（parallel_extra 截断补抓）；
- 所以新增 1000 条的可行来源只有 **kanbun.info 新栏目**。sitemap 实测：
  站点栏目 = koji（故事，已用尽）/ keibu（経部只有 論語/大学/孝経 三个 index，
  已用尽）/ **syubu（集部：漢詩 kanshi + 唐詩選 toushisen + 歴代 reki_* + 詩人別
  shijin_{a..ra} 8 索引 + 詩経 shikyo_*，全部未用）**/ shibu01-02（404 死链）/
  miscellaneous（介绍页）。

## 2. 抓取（`tools/night57_scrape_syubu.py` → `eval/night57_scraped_syubu.json`）

- 结构与 D16 大学/孝経相同（genbun01 + yomi02/yomi03 相邻对）；
- 解析同款（剥 ruby `<rt>/<rp>` + 去标签 + 去空白 + 去页头计数；**expected 一字不改**）；
- 顺序：詩経 shikyo_*（11 页，経文气质优先）→ 詩人別内容页 → 歴代/唐詩選；
- 限速 0.4s + 重试 3 次；203 页 / **1101 对** / 819 秒（詩経 102 + 漢詩 999）；
- 抓取中的推销页（如 boshu03，honbun02 结构）自然 0 对跳过。

## 3. golden_3000（`tools/night57_build_golden_3000.py`）

```
total 3000 | uniq ids 3000 | uniq hakubun 2975（golden_2000 的 25 条内部重复原样保留）
新增 1000 = parallel_extra 31 + 詩経 102 + 漢詩 867（skipped dup_hakubun 93）
新增分档: ≤20字 997 / 21-40字 3        ← 诗是短句，构成注意（同 D16 §3.2 教训）
```
- 硬断言：`combined[:2000]` 与 golden_2000 逐条 dict 相等且顺序一致（构建时 + 
  `tests/test_golden_3000.py` 双保险）；
- 文体全景：故事 1333 / 論語 362 / 大学 189 / 孝経 147 / **詩経 102 / 漢詩 867**。

## 4. 规则引擎全跑（`tools/night57_eval_3000.py`，98 秒，D/E/F/G 全链）

```
engine OK 2999 / error 1 | 精确 15/2999 | avgDist 16.321
分档  ≤20字 8.390(2042)  21-40字 21.838(542)  41-60字 37.296(247)  >60字 64.077(168)
文体  故事 21.197  漢詩 7.247  論語 26.956  大学 14.603  孝経 9.286  詩経 5.206
```
- **确定性对照（本夜最强证据）**：前 2000 条重跑输出 vs day17 真机归档
  **输出文本不同行数 = 136，恰为 Rule G 的改写行数**；前 2000 avgDist **20.916
  与 N55 离线预测逐位一致**（127 改善 / 0 变差 / 1873 持平）——API 全链与
  离线真函数逐位等价，第三次得到同一结论（D17 §6、N55 §8 之外）。
- 唯一 error：`toushisen135-12`（應知黃綺心）—— **MeCab 词典缺 `應` 的助動詞
  token（KeyError 應,v,助動詞,必要,*）**，引擎层缺口（guwenbert 路径同一条同样失败），
  非规则问题，如实入档。
- 詩経 5.206 / 漢詩 7.247 都低——**构成警告**：两者 100% 是 ≤20 字短句
  （詩句白文 4-6 字），不能读成「引擎擅长漢詩」（N56 方法论的直接应用）。

## 5. guwenbert 新增段（`tools/night57_guwenbert_new.py`，离线，1127 秒）

```
规则引擎（新增1000 有效 999）  avgDist 7.122  精确 6
guwenbert（同 999）           avgDist 7.075  精确 5
逐条对决：规则更好 306 | guwenbert 更好 325 | 持平 368   ← 五五开
分档（≤20字 996 条）：规则 7.078 vs guwenbert 7.03；21-40字 3 条：21.667 vs 21.00
```
与 D16（旧新增段 +0.327、330/325 五五开）同型：**平均差 <0.05（0.7%），逐条各有
胜负**。规则引擎快 ~1100 倍（98s/3000 条 vs 19min/1000 条）。「要不要接 guwenbert」
仍是 D16 时留的产品拍板，本夜数据不改变该结论。

## 6. 本夜改动清单

| 文件 | 性质 |
| --- | --- |
| `eval/golden_3000.json` / `golden_3000_stats.json` | 新评测集（前 2000 字节级保留） |
| `tools/night57_scrape_syubu.py` / `night57_build_golden_3000.py` / `night57_eval_3000.py` / `night57_guwenbert_new.py` / `night57_compare.py` / `night57_h2h.py` / `night57_error_row.py` | 抓取/建库/评测/对照 |
| `tests/test_golden_3000.py` | +3 条完整性测试 |
| `eval/night57_scraped_syubu.json` / `night57_results_3000.json` / `night57_guwenbert_new1000.json` / `*.txt` | 证据 |
| `REPORT_NIGHT57.md` / `tools/night57_append_shift.py` / `SHIFT_LOG.md` | 报告与夜志 |

## 7. 验证汇总

- pytest **172 → 175 passed**（+3 test_golden_3000）；
- `python tools/accept_night.py 57` 通过；
- GT CER：本夜**零 backend 代码改动**（新增的只有 eval 数据与 tools 评测脚本），
  N55 当夜 GT 实测（raw 0.3568 / norm 0.3053 逐位不变、N49 归档 sha256 不变）直接覆盖；
- expected 一字不改：抓取器与 D16 同款「剥 ruby/标签+去空白」，golden_2000 前缀
  由构建断言 + pytest 双重锁定。

## 8. 待拍板（编号 = 下一班的下单清单）

1. N52-54 的 ④-⑧、N55 的 1-3 原样保留；
2. **新增 ⑨**：golden_3000 要不要登记进 `accept_night.py` 的 `NIGHT_ARTIFACTS`
   （会启用 eval_integrity 检查——需要 id 唯一/自报数一致的结构，当前文件是纯
   list 形状，登记前要先统一形状）；以及 3000 条要不要成为新的默认评测口径
   （对比基准从 night31 系列切到 night57 系列）；
3. **新增 ⑩**：引擎词典缺「應」token（toushisen135-12，KeyError）——要不要在
   白文预处理把舊字体「應」归一成「応」再进引擎（会改评测输出，需重跑口径，
   拍板后再做）。

## 9. 禁止事项自查

未发图/未读图/未抄 GT ✓；未改 `eval/ocr_gt_100.tsv`、`eval/golden*.json`
（golden_2000 原样、只**新增** golden_3000）✓；未重跑 47 页全本 OCR ✓；
未碰 Night 9、16-20 ✓；未动 N51-55 拍板项 ✓；expected 一字未改 ✓；
本地提交不推远程 ✓；心跳按小时二进制追加 ✓。
