# REPORT_NIGHT59

## 0. 一句话结论

「應」调查完成（**只诊断、零代码改动**）：缺的不是 N57 定性的「MeCab 词典缺 token」，
而是 **udkundoku 活用表 `udkundoku/auxiliary.py` 的 AUX 缺 lemma「應」条目**
（25 键里唯一缺，MeCab 词典其实**有**應 token）；**「應→応 白文预处理」被实证为
完全 no-op**（18 行逐字节不变、error 照旧——新字体応的 lemma 也是應），N57 拍板项
⑩ 的预设方案无效；真正的修复 = AUX 补 1 条（内存对照：该行 dist 4、其余 2999 行
逐字节不变、0 新 error、幂等），**是否打这个引擎层补丁 = 新拍板项 ⑬**。

## 1. 开工核对

- `git log -1` = `6ec7fca`（N58 收尾）✓；pytest 190 passed（N58 终态）✓；
- 本夜**不改引擎、不改 backend、不改评测数据**——全部产出为 tools 诊断脚本 + eval 证据。

## 2. 复现与定位（`tools/night59_repro.py` → eval/night59_repro.txt）

错误行 toushisen135-12（白文「應知黃綺心」，expected「応に黄綺の心を知るべし」），
API 实际返回 `{"detail":"訓読処理失敗: KeyError('應,v,助動詞,必要,*')"}`（用户可见的
訓読処理失敗，整条请求失败）。

三层定位：

| 层 | 舊字体「應知黃綺心」 | 新字体「応知黄綺心」 | 结论 |
| --- | --- | --- | --- |
| 原生 MeCab（mecab-kanbun） | `應` → `v,助動詞,必要,*,*,*,應/应,AUX,Mood=Nec,ought` | `応` → 同一 feature | **词典有應 token，还带活用语义**（N57「词典缺 token」定性不成立） |
| udkanbun 解析 | token 正常（xpos `v,助動詞,必要,*`，lemma `應`） | token 正常，**lemma 也是 `應`** | 两形态解析等价，lemma 归一到舊字形 |
| udkundoku.translate | **KeyError `應,v,助動詞,必要,*`** | **同一个 KeyError** | 失败在 AUX 活用表查键：键 = lemma + xpos |

**AUX 表本体**（`tools/night59_aux_probe.py` → eval/night59_aux_probe.txt）：
`udkundoku/auxiliary.py` 共 25 键；`v,助動詞,必要` 组只有 **儀/宜/須** 三个 lemma
（值 `'べから:べく:べし:べき:べけれ:べけれ'`），**没有應**。含「応」的键也为 0——
新字体surface 一样救不了。

## 3. 全库扫描（`tools/night59_scan.py` → eval/night59_scan.json）

- golden_3000 全部 hakubun 过原生 MeCab，枚举 `v,助動詞` token：13 个
  (lemma, xpos) 组合、共 509 行含助動詞 token——**12 组 AUX 全覆盖，唯一缺的就是
  `應,v,助動詞,必要,*`，且全库只涉及 1 行**（toushisen135-12）。可/能/欲/敢/得/足/
  須/見/宜/肯/被/儀 全部正常；
- 含「應」的 hakubun 共 **18 行**：除 135-12 外，17 行都是名詞/動詞用法（應對・
  應接・應是・應乎人…），全部可解析且输出已被 N3 显示层转成 応（expected 含應
  0 行、got 含應 0 行——kanbun.info 从不写舊字体，输出层已有映射）；
- 舊字体盘点：**1756/3000 行 hakubun 含至少 1 个 SHINJITAI_MAP 旧形字**（爲 369 行、
  與 195 行…），全部可解析——旧字体本身不是缺陷源，缺的是特定 lemma 的活用表条目。

## 4. 「應→応 白文预处理」离线模拟（`tools/night59_sim.py` → eval/night59_sim.json）

对 18 行含應 hakubun，原始 vs 预处理後各走与 main.py 逐位一致的完整行链
（ENGINE → merge_proper_nouns → translate → style_fix_with_hakubun →
normalize_shinjitai）：

```
仍 error（同 KeyError）: 1 行 ['toushisen135-12']
error 被预处理修复     : 0 行
输出被预处理改变       : 0 行（17 行逐字节不变）
语料外 4 探针          : 逐字节不变（應對進退/反應/應長思之/控制组）
```

**结论：预处理是纯 no-op 且不修复**——lemma 不变（応→應），AUX 查键照样缺。
副作用面 = 0（输出一点不动），收益面 = 0。**N57 拍板项 ⑩ 的预设「應→応 归一」
应予否决**：不做，与「会改评测输出需拍板」相比，实证是「改了也没用」。

## 5. 真正的修复长什么样（`tools/night59_aux_patch_probe.py`，**内存对照、零落盘**）

把 `udkundoku/auxiliary.py` 的 AUX 补 1 条（值照抄同 xpos 的須），**只在内存**：

```python
AUX["應,v,助動詞,必要,*"] = AUX["須,v,助動詞,必要,*"]   # 'べから:べく:べし:べき:べけれ:べけれ'
```

- toushisen135-12：KeyError → 「**黄の綺心を知るべし**」，dist **4**（非逐字节命中：
  expected「応に黄綺の心を知るべし」的「応に」前缀来自词典 Mood=Nec，AUX 值只管
  べ形活用，引擎不给前缀——dist 4 = 応に(2)+黄綺の心(1)+节奏差，如实记录）；
- **全库回归：3000 条重跑，其余 2999 行逐字节不变、0 新 error、幂等**——补丁是
  纯增益，无一行被搅动；
- 错误类不再是「1 条评测行的孤例」：**任何用户输入含助動詞用法的「應」（乃至将来
  扩语料）都会让整条 API 请求失败**（`訓読処理失敗: KeyError`）。

## 6. 拍板依据（⑩ 否决 + 新增 ⑬）

| 选项 | 实证效果 | 副作用 | 建议 |
| --- | --- | --- | --- |
| ⑩ 白文预处理 應→応 | **0**（no-op，不修复） | 0 | **否决**（N57 预设被本夜推翻） |
| ⑬-a AUX 补条目（引擎层，1 条） | 该行 dist 4、error 1→0 | 其余 2999 行逐字节不变（实证） | **建议采纳**，但这是引擎行为变更=拍板 |
| ⑬-b AUX 补条目（同 xpos 儀/宜/須 4 lemma 一起补齐预防性） | 当前语料 0 收益 | 同上，0 变差风险（同值） | 可选（防将来语料出現 儀/宜 未覆盖活用） |
| 放着不修 | 3000 条评测 error 1 永存 | 用户输入含應=整条请求失败 | 不建议 |

⑬ 的实现路径二选一（等拍板）：(a) `backend/main.py` import 处 2 行 runtime 补丁
（不动 site-packages，sidecar 打包无感）或 (b) 直接补 `site-packages/udkundoku/
auxiliary.py`（第三方文件改动，重装环境会丢，需记录）。若拍板采纳，夜里做时按
Night 22 门径走：pytest 锁（补丁前后行为断言）+ 3000 条重跑对照 + GT 门。

## 7. 验证汇总

- 本夜 **零 backend/eval 数据改动**：pytest 190 passed 维持（跑一次确认）；
- GT 门：零 backend 代码改动（只有 tools/eval 证据新增），N58 当夜 GT 实测
  （raw 0.3568 / norm 0.3053 逐位不变、night49 归档 sha256 `ff21e4fa…`）直接覆盖；
- 诊断过程未触碰引擎文件（auxiliary.py 只 import 读取，内存补丁进程结束即消失，
  site-packages 无任何改动——`night59_aux_patch_probe.txt` 有撤销断言记录）。

## 8. 禁止事项自查

未发图/未读图/未抄 GT ✓；未改 `eval/ocr_gt_100.tsv`、`eval/golden*.json` ✓；
未重跑 47 页全本 OCR ✓；未碰 Night 9、16-20 ✓；**未改引擎**（任务书红线：只诊断）
——MeCab/udkundoku/udkanbun 三个包零改动 ✓；expected 一字未改 ✓；
本地提交不推远程 ✓；心跳按小时追加 ✓。

## 9. 待拍板（编号 = 下一班的下单清单）

1. N52-57 全部既有拍板项原样保留；
2. **⑩ 更新**：「應→応 白文预处理」实证无效（no-op）→ 建议从拍板清单改为
   **否决结案**；
3. **新增 ⑬**：AUX 补 1 条（應,v,助動詞,必要,* = 須 同值）要不要上——引擎行为
   变更，实证 0 副作用 + 修复 1 条评测 error + 消灭一类用户输入 500；实现路径
   (a) backend runtime 2 行 / (b) site-packages 补丁，二选一。

## 10. 改动清单

| 文件 | 性质 |
| --- | --- |
| `tools/night59_repro.py` / `night59_aux_probe.py` / `night59_scan.py` / `night59_sim.py` / `night59_aux_patch_probe.py` | 复现/AUX 表定位/全库扫描/预处理模拟/内存补丁对照 |
| `eval/night59_repro.txt` / `night59_aux_probe.txt` / `night59_scan.json(.txt)` / `night59_sim.json` / `night59_sim_result.txt` / `night59_aux_patch_probe.txt` / `night59_patch_stdout.txt` | 证据 |
| `REPORT_NIGHT59.md` / `SHIFT_LOG.md` | 报告与夜志 |

## 11. 复现

```bat
set PATH=D:\Python312;D:\Python312\Scripts;D:\nodejs;D:\Git\cmd;%PATH%
python -I tools\night59_repro.py            :: 三层复现定位
python -I tools\night59_aux_probe.py        :: AUX 表 25 键盘点
python -I tools\night59_scan.py             :: 全库助動詞 lemma × AUX 覆盖
python -I tools\night59_sim.py              :: 應→応 预处理模拟（no-op 实证）
python -I tools\night59_aux_patch_probe.py  :: 内存补丁对照（零落盘）
```
