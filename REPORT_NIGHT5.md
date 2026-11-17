# REPORT_NIGHT5.md — Night 5（2026-11-17 值班段）

按 ROADMAP.md Night 5 执行：訓読质量第二轮（模型路线 + 规则第二轮）。

---

## 1. guwenbert 对比 —— 1.5 小时预算内止损，未跑成（根因链完整记录）

**模型已在位**（Night 3 下载成功，463.5MB，
`D:\Python312\Lib\site-packages\udkanbun\supar-kanbun\guwenbert-base.supar`），
本夜做了系统性的失败定位，全部真实报错留档：

1. **训练侧证据**（仓库 `mkmodel.sh`）：
   `pip install supar@git+https://github.com/yzhangcs/parser` + **torch 1.6.0**（2022 年代），
   训练命令 `python3 -m supar.cmds.biaffine_dependency train -f bert --bert ethanyt/$M`。
   → checkpoint 是 git 版 supar（2022 HEAD）序列化的，不是 PyPI `supar` 包。
2. **PyPI supar 1.1.4**：模型可加载（`Loading weights: 199/199`，tokenizer 经
   `HF_ENDPOINT=https://hf-mirror.com` 从 ethanyt/guwenbert-base 拉取成功），
   但 predict 阶段 `supar/models/model.py:141 feat_embeds.append(self.bert_embed(feats.pop(0)))`
   → **IndexError: pop from empty list**。输入格式字符串 / 词列表 / 普通句列表 / conllu
   文件路径四种姿势全试，同一报错。
3. **根因定位**：加载后 `parser.transform.fields` =
   `['ID','FORM','LEMMA','CPOS','POS','FEATS','HEAD','DEPREL','PHEAD','PDEPREL']`
   ——**没有 bert 字段**。即 PyPI supar 1.1.4 的 load()/Dataset 管线与
   git-2022 checkpoint 的 Field 结构不兼容（模型权重要 bert feats，数据管线不产生）。
4. **supar==1.1.2** 同一失败；**1.1.0 的 wheel 本身有打包 bug**
   （`file outside the target directory`，安装失败，1.1.4 被连带卸载——当前环境装的是 1.1.2）。

**结论**：PyPI 全系 supar 与该 checkpoint 不兼容。下一夜的正确路线（按成本排序）：
a) `pip install git+https://github.com/yzhangcs/parser@<2022 年的 commit>`（训练同代代码）；
b) 或手写加载器：`DepParser.build(**checkpoint_config, bert='ethanyt/guwenbert-base')`
   构造带 bert 字段的 transform，再 `model.load_state_dict(state['state_dict'])` 注入权重；
c) 或放弃 supar 管线，用 transformers 直接对 ethanyt/guwenbert-base 做依存头分类（工作量大）。
**探针脚本已留在 repo**：tools/probe_supar_file_predict.py、tools/probe_supar_list_predict.py。

## 2. qkana 官方源再试一次 —— 仍未成功（半阻断细节更新）

`tools/fetch_official_qkana.py` 再试：服务器**支持断点续传**（Range 请求返回正确的
剩余长度 Content-Length: 268,003,068 = 总 294,217,468 − 已传 26,214,400），但 body 在
26MB 处再次停滞（数分钟 0 增长），按预算杀掉。结论不变：需要可达 NINJAL 的网络，
脚本+续传已备好，26MB 的 .part 保留在 ocr_runtime/（下次续传起点）。

## 3. 规则第二轮 —— Rule C 干净落地

Night 4 的分类把 助词错(92%)/切分错(90%) 列为 top2，且指出「依存分析层面的活用差异
字符串规则不可安全覆盖」。本夜从 full_v2 的 diff 里挖掘到唯一一个**方向完全一致**的
高频模式并落地：

- **Rule C：「て而して」→「て」**（backend/kundoku_rules.py `style_dedup_shite_soshite`）
  - 证据：`tools/measure_rule_candidate.py` 测量——200 条里命中 26 条，
    **26/26 处 expected 都是「〜て」直接续接**（而を重复接续助词として使わない；
    2 处"expected 有而"的疑似反例经人工核对是 而も/而るに 等别位置的假阳性）。
  - 上线后 full_v3 实测：**26 条改善 / 0 条变差 / 174 条持平**——与预测命中数完全一致。

再読文字「未」以外（應・當・須・蓋・宜・將）：扫描 200 条的 got/expected，本语料中
没有出现可修的再読文字句式（engine 对这些字的处理未在 diff 里形成可修模式），如实记录：
本夜未做。高频动词活用表：活用差异（飲めば vs 飲す 等）属 mecab-kanbun 词条/解析层，
字符串规则会引入同等数量的错误，不做——等 guwenbert 路线修通后由依存分析解决。

## 4. 200 条四轮对比（同一把归一化尺子，tools/compare3.py / eval_summary.py）

| 运行 | 规则 | 精确匹配 | 平均编辑距离 |
| --- | --- | --- | --- |
| `night4_results_baseline.json` | 无（引擎原始） | 0/200 | 22.14 |
| `night4_results_full_v1.json` | Night3 规则集 | 0/200 | 21.36 |
| `night4_results_full_v2.json` | + Night4 Rule A/B | 0/200 | 21.02 |
| `night5_results_full_v3.json` | + Night5 Rule C | **0/200** | **20.48** |

- full_v3 vs full_v2：**改善 26 / 变差 0 / 持平 174**。
- full_v3 vs 基线（累计）：**改善 130 / 变差 6 / 持平 64**。
- 10 条子集单独一行：基线 0/10、v1 0/10、v2 0/10、v3 0/10。
- 分类变化（full_v3）：助词错 188 (94%)、切分错 169 (84.5%)、专名错 2。
- 精确匹配仍 0/200——残差集中在依存解析（助词插入位置、名词化、活用），字符串层收益已尽。

## 5. 做到哪 / 卡在哪 / 下一步建议

Night 5 完成（guwenbert 按预算止损、规则 C 落地、qkana 记录）。无未决卡点。下一步建议：
1. **guwenbert 收尾**（第一优先）：按 §1 的 a/b 两条路线之一，训练同代 supar 或
   手写带 bert transform 的加载器——模型/网络/验证都已就位，只差加载器 ~50 行代码。
2. 合并手术加护栏（Night 4 遗留：toranoi-1/ichiji 系 6 条变差的根因）。
3. qkana：仅需可达 NINJAL 的网络跑 `tools/fetch_official_qkana.py`（续传起点 26MB）。

## 6. 禁止事项自查

未改 expected；guwenbert「模型加载成功」与「对比未跑成」分开如实写；qkana 失败细节原样记录；
规则 C 的 26/26 预测与实测一致（未夸大）；无 key/token 入库；只本地提交。
