# REPORT_DAY1.md — 白天 D1：guwenbert 加载器（2026-11-18）

任务单：白天清单 D1（100milionseek / deepseek-v4.1-flash-free）。
起点：`git log -1` = `90ec05e night13: cargo build done, exe 7.4MB; night21 report bucket stats update`；
开工前 `pytest tests/test_api.py -q` = **14 passed**（11.79s）。

**结论：跑通了。** 加载成功 + 「王顧左右而言他」依存解析输出真实结果（见 §4），
并使用「随机初始化对照组」验证权重确实生效（见 §5）。`pytest` 收尾仍 14 passed。

---

## 1. 根因修正——Night 5 的判断需要更新一处

REPORT_NIGHT5.md §1 写道「PyPI supar 1.1.4 的 load()/Dataset 管线与 git-2022 checkpoint
的 Field 结构不兼容（transform 里没有 bert 字段）」。本次逐项 dump 后，更精确的说法是：

| 观察 | 实测 |
| --- | --- |
| checkpoint 的 `transform.FORM` | `(Field('words'), SubwordField('bert'))` — **bert 字段在**，位于 FORM 内部 |
| 缺的是什么 | 2022 版 `biaffine_dep.build()` 里还有一个 `TEXT = RawField('texts')`，`FORM=(WORD, TEXT, CHAR, ELMO, BERT)`。本 checkpoint **没有** texts |
| 1.1.2 的 `_predict` | `words, texts, *feats = batch`（supar/parsers/dep.py:216） |
| 后果 | batch 顺序是 `[words, bert]`，于是 `bert` 被当成 `texts`，`feats` 是空列表 → `model.py:141 feats.pop(0)` → **IndexError** |
| 另一个隐藏问题 | state_dict 是 2022 键名（`feat_embed.*` / `lstm.*` / `mlp_arc_d.*`），1.1.2 的模型属性叫 `bert_embed.*` / `encoder.*` / `arc_mlp_d.*`。`Parser.load` 用 `strict=False`，所以不会报错，只会**静默丢权重** |
| 还有一处 | 2022 的 `args.feat_pad_index = 1`（BERT 词表里 `[PAD]` 的下标），1.1.2 对应参数名是 `bert_pad_index`；漏掉会让 mask 全错 |

也就是说 Night 5 里「模型加载成功但 predict 报 IndexError」的两个阶段，
**根因是同一个字段错位**，不是权重或版本不兼容到的程度。改字段顺序即可。

## 2. 做法（tools/load_guwenbert.py）

三步，都不动 PyPI supar 的源码：

1. **重建 transform**：拿 checkpoint 自带的 `Field('words')`、`SubwordField('bert')`
   （含 4728 词表 / 23292 BERT 子词表 / fix_len=20 / pad=`[PAD]`），
   中间插入 `RawField('texts')` 占位 → `CoNLL(FORM=(words, texts, bert), HEAD=..., DEPREL=...)`。
   这样 batch 解包顺序变成 `words, texts, *feats`，feats 里正好是 bert。
2. **构造模型 + 映射键名**：`BiaffineDependencyModel(**mapped_args)`，然后把
   `state['state_dict']` 的 238 个键按前缀表映射（见脚本 `KEY_PREFIX_MAP`）后
   `load_state_dict(strict=False)`。参数映射里 `feat_pad_index → bert_pad_index`、
   `n_mlp_arc/n_mlp_rel → n_arc_mlp/n_rel_mlp`、`lstm_dropout → encoder_dropout`。
3. **直接用 1.1.2 的 predict 管线**：字段既然对齐了，就不需要自己写 decode。

分词用 udkanbun 自带的 `mecab-kanbun` 词典（`udkanbun.load()` 走的就是它），
保证切分与训练语料一致；也可用 `--words` 显式传分词。

加载记录（脚本直接打印）：

```
[load] name=biaffine-dependency  feat=bert  bert=ethanyt/guwenbert-base
[load] flattened (eval) = ['words', 'texts', 'bert']
[load] state_dict: 238 keys -> 238 mapped
[load] missing(0) = []
[load] unexpected(1) = ['bert_embed.bert.embeddings.position_ids']
[load] weights covered: 237/237 model tensors
```

- `missing = 0`：模型 237 个张量全部拿到值。
- 唯一 unexpected 是 `position_ids`，这是 transformers 的 buffer，不参与前向，正常。
- tokenizer 走已落盘的 HF 缓存（`models--ethanyt--guwenbert-base`，Night 3 下的），
  设 `HF_ENDPOINT=https://hf-mirror.com` + `HF_HUB_OFFLINE=1`，**本次未产生任何网络请求**
  （首次盲试时未设离线，huggingface.co 连接超时 5 次重试后失败，与记忆里 hf 抖动一致；
  设离线后直接命中缓存）。

## 3. 模型规格（从 checkpoint 读出，非推测）

- 结构：BiLSTM（3 层，hidden 400，双向）+ BERT 特征（guwenbert-base，768 维，
  用最后 `n_bert_layers=4` 层做 ScalarMix，投影到 100），biaffine 依存。
- 词表 4728 / 关系标签 41（含 `<bos>`/`<pad>` 等特殊符）/ BERT 子词表 23292。
- 权重文件 463.5MB，`state_dict` 238 个张量。

## 4. 「王顧左右而言他」真实输出

分词（mecab-kanbun）：`王 / 顧 / 左 / 右 / 而 / 言 / 他`

```
 ID  FORM   HEAD  DEPREL
  1  王         2  nsubj
  2  顧         0  root
  3  左         2  obj
  4  右         3  flat
  5  而         6  cc
  6  言         2  conj
  7  他         6  obj
```

```
ROOT
└─ 顧  [root]
   ├─ 王  [nsubj]
   ├─ 左  [obj]
   │  └─ 右  [flat]
   └─ 言  [conj]
      ├─ 而  [cc]
      └─ 他  [obj]
```

语言学上说得通：「王」是「顧」的主语，「左」「右」是「顧」的宾语（左右=左右看），
「而」连接「顧」与「言」，「他」是「言」的宾语——正是「顧左右而言他」。

另跑一句交叉验证（「學而時習之」）：

```
1 學 root | 2 而 cc→3 | 3 時 conj→1 | 4 習 flat:vv→3 | 5 之 obj→3
```

`學` 作根、`時` 作 `conj`、`習` 挂 `flat:vv`——「時習」被当作复合动词处理，
这是该树库的标注习惯（`flat:vv`），不是加载错误。

## 5. 反证：权重真的生效了吗

只看到「输出合理」不够——如果 `load_state_dict` 全部静默失败，也可能输出垃圾。
做了对照组：同一 transform、同一句，模型**随机初始化**（`torch.manual_seed(0)`，不注入权重）：

| 模型 | 输出 |
| --- | --- |
| 注入 checkpoint 权重 | `王→2 nsubj, 顧→0 root, 左→2 obj, 右→3 flat, 而→6 cc, 言→2 conj, 他→6 obj` |
| 随机初始化 | `王→0 <bos>, 顧→1 <bos>, 左→1 <bos>, ...`（全部指向 1 号节点，标签全是 `<bos>`） |

`SAME_PRED = False`。随机模型退化成常量输出，说明真实输出只能来自注入的权重。

## 6. 耗时（本机 CPU）

| 阶段 | 耗时 |
| --- | --- |
| `load_parser`（读 463.5MB + 从 HF 缓存建 BERT） | **44.2 s** |
| MeCab 分词（mecab-kanbun） | 0.02 s |
| 单句 predict（7 词） | **0.6 s** |

加载 44s 是一次性成本，进程内复用即可；如果接进后端，应该在 FastAPI startup 里预热，
不要在请求路径里加载。

## 7. 验收

- `python tools/load_guwenbert.py` 退出码 0，输出上表结果。
- `python -m pytest tests/test_api.py -q` → **14 passed**（本次新增文件不影响后端）。
- 未改 `expected`、未改评测数据、未推远程、无 key/token 入库。

## 8. 已知限制 / 下一步

1. **只验证了「能跑」，没验证「好不好」**。尚未在 200 条评测集上跑对比，
   所以**不能**说 guwenbert 比现有规则引擎好——需要下一步做 full_v4 对比（用
   `tools/compare3.py` 同一把尺子），这和 Night 5 §4 的表格才对得上。
2. checkpoint 里 `args.device='cuda'`，本机无 GPU，脚本强制落到 cpu。
   BERT 前向在 CPU 上单句 0.6s，长句会更慢（要按 max_len=512 分块）。
3. `transform.training` 被 pickle 成 `True`；predict 里 `transform.eval()` 会处理，
   但如果将来复用 transform 做别的事，注意这个状态。
4. 依赖 transformers 4.57.6 + torch 2.15.0+cpu，脚本里有两条 deprecated warning
   （`apply_permutation`、非元组索引），不影响结果，将来升 torch 2.9 会变成错误，
   届时需固定版本或改 supar 内部（仓库外，注意 qkana shim 的同类风险）。

## 9. 禁止事项自查

未改 expected；「加载成功」与「解析输出」都是脚本原样打印，未手改；
根因部分明确标注是对 Night 5 报告的一处**修正**（bert 字段其实在，缺的是 texts），
没有把 Night 5 的结论说成错的、也没有照抄；未推远程、未新建仓库；
报告中无任何 key/token/个人信息。
