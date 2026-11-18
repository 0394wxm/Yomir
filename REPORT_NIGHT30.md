# REPORT_NIGHT30.md — Night 30：字符级替换热图 → 正字化表扩充 40 对（2026-11-19 凌晨）

Night 28/29 语料库的第一个规则级产出：got/exp 字符级替换热图暴露出 SHINJITAI_MAP 的
**40 个标准新字体缺口**，离线模拟 **-0.39、433 改善 / 0 变差**，幂等 40/40，
官方重评 **24.77 → 24.38（与模拟逐位一致）**。

起点：`git log -1` = `4a9eeb7`。产物：`tools/night30_char_heatmap.py`、
`night30_sim40.py`、`eval/night30_char_heatmap.json`、`eval/night30_results_parallel.json`
（官方归档）、`backend/kundoku_rules.py`（SHINJITAI_MAP 77→117 条）。

---

## 1. 热图发现（night29 归档 1705 条，difflib 1:1 替换块）

- 汉字→汉字 1:1 未映射替换 **368 处**，top：**學→学 105、樂→楽 41、德→徳 36**、
  號→号 8、發→発 8、廢→廃 8……主力是論語/儒家语的旧字体（Night 3 的表只收了
  当时 50 条语料里出现的 22 对，後续夜里語料扩大暴露了缺口）。
- 汉字→假名 top：**而→に 74 处**（にして 盲区的字符级形态，Night 25/27 结论的旁证）；
- 假名→汉字 top：べ→可 75、ま→亦 57、そ→夫 34（可らず/亦た/夫れ 等 hypthetic
  约定，解析层，不动手）。

## 2. 上线内容与验证链

**SHINJITAI_MAP 新增 40 对**（77→117）：count≥2 的全部未映射标准新字体对。
逐条为当用/常用汉字表标准简化（學学/樂楽/德徳/號号/發発/廢廃/莊荘/乘乗/讀読/關関/
聲声/黨党/輕軽/稱称/斷断/讓譲/懷懐/拜拝/佛仏/晉晋/亂乱/劍剣/寶宝/勞労/龜亀/齒歯/
閒間/鄰隣/帶帯/殘残/藝芸/蟲虫/蠻蛮/恆恒/臺台/來来/賣売/條条/默黙/彌弥），
不是逐条过拟合——count≥1 的 56 个低频对**没有**收（其中可能混入非标准对应，
等热图证据积累）。

验证链（每步独立可复跑）：

1. **离线模拟**（night30_sim40.py，1705 条）：24.77→24.38（-0.39），改善 433 / **变差 0**；
2. **码位核查**：40 对无 identity bug（我第一版手写幂等自检的期望串自己写错了字，
   程序化核查 40/40 正常——教训：形近字一律程序比对，不目测）；
3. **幂等**：40/40 程序化验证 + 整表幂等（M == {k: M.get(v,v)}) 为 True；
4. **pytest 33 passed**（含经典句/护栏/门 4c 抽查）；
5. **官方重评**：`run_eval_parallel.py night30_results_parallel.json` →
   **24.38、1705/1705 OK、精确 4/1705 不变**，与模拟逐位一致。

## 3. 没做的（如实）

- **count≥1 的 56 个低频对未收**（含 澄→?、逐条核对成本高且收益 <0.05，等下一轮热图）；
- 汉字↔假名方向（べ→可 75 等）：解析层产出，显示规则动不了（ Night 25/27 同门）；
- 而→に 74 处：にして 盲区的另一种统计口径，Night 27 已关闭，不重开。

## 4. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\night30_char_heatmap.py   :: 热图 → eval/night30_char_heatmap.json
python -I tools\night30_sim40.py          :: 40 候选整体模拟（-0.39 / 433 / 0）
python -m pytest tests -q                 :: 33 passed
python -I tools\run_eval_parallel.py night30_results_parallel.json  :: 官方重评 24.38
python tools\accept_night.py 30           :: 验收门
```

## 5. 禁止事项自查

expected 一字未动（热图只看 got/exp 的对齐，不改数据）；候选逐条为标准新字体
且模拟 0 变差才上线（Night 3 的"变差即移除"纪律延续）；幂等程序化验证
（目测自检的第一个版本是错的，已自抓并以程序版为准）；count≥1 低频对如实说明
未收的原因；无 key/token；只本地提交。
