# -*- coding: utf-8 -*-
"""guwenbert-base.supar 手写加载器（绕过 PyPI supar 的 load/predict 管线不兼容问题）。

背景（REPORT_NIGHT5.md §1）：
  * PyPI supar 1.1.x 的 `Parser.load()` 能读 checkpoint，但 predict 阶段
    `IndexError: pop from empty list`（supar/models/model.py:141）。
  * 根因不是权重问题，而是数据管线错位：checkpoint 的 `transform.FORM`
    是 `(Field('words'), SubwordField('bert'))` 两个字段，**没有** 1.1.x
    所预期的 `texts`（RawField）。于是 `_predict` 里的
    `words, texts, *feats = batch` 把 bert 张量当成 texts，feats 为空。
  * 另外 checkpoint 的 state_dict 是 2022 版 supar 的键名
    （feat_embed.* / lstm.* / mlp_arc_d.*），与 1.1.x 的
    （bert_embed.* / encoder.* / arc_mlp_d.*）不同。

本加载器的做法：
  1. 用 checkpoint 里自带的 Field/vocab，重建一个 **带 texts 占位字段** 的
     CoNLL transform；
  2. 用 checkpoint 的 args 构造 1.1.x 的 BiaffineDependencyModel；
  3. 把 state_dict 的 2022 键名映射成 1.1.x 键名后 load_state_dict；
  4. 直接用该 parser 的 predict 管线（此时字段顺序已对齐）。

用法：
    python tools/load_guwenbert.py                 # 跑默认例句
    python tools/load_guwenbert.py 王顧左右而言他    # 自定义句子（MeCab 分词）
    python tools/load_guwenbert.py --words 王 顧 左右 而言 他
"""

import argparse
import os
import sys

# 本机 huggingface.co 不可达，统一走镜像；模型已在 HF 缓存里，优先离线。
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

import dill
import torch

from supar.models import BiaffineDependencyModel
from supar.parsers.dep import BiaffineDependencyParser
from supar.utils.field import RawField
from supar.utils.transform import CoNLL

SITE_PACKAGES = os.path.dirname(os.path.dirname(torch.__file__))
DEFAULT_CKPT = os.path.join(SITE_PACKAGES, 'udkanbun', 'supar-kanbun', 'guwenbert-base.supar')

# 2022 版 supar -> PyPI supar 1.1.x 的模块/参数名前缀映射
KEY_PREFIX_MAP = (
    ('feat_embed.', 'bert_embed.'),
    ('lstm.', 'encoder.'),
    ('mlp_arc_d.', 'arc_mlp_d.'),
    ('mlp_arc_h.', 'arc_mlp_h.'),
    ('mlp_rel_d.', 'rel_mlp_d.'),
    ('mlp_rel_h.', 'rel_mlp_h.'),
)


def map_state_key(key):
    for old, new in KEY_PREFIX_MAP:
        if key.startswith(old):
            return new + key[len(old):]
    return key


def build_model_kwargs(args, device):
    """把 2022 版 checkpoint 的 args 映射成 1.1.x 的构造参数。"""
    feat = args.feat
    if isinstance(feat, str):
        feat = [feat]
    else:
        feat = list(feat)

    return dict(
        n_words=int(args.n_words),
        n_rels=int(args.n_rels),
        n_tags=None,
        n_chars=None,
        encoder='lstm',
        feat=feat,
        n_embed=int(args.n_embed),
        n_feat_embed=int(args.n_feat_embed),
        n_char_embed=int(args.n_char_embed),
        n_char_hidden=int(getattr(args, 'n_char_hidden', 100)),
        char_pad_index=0,
        bert=args.bert,
        n_bert_layers=int(args.n_bert_layers),
        mix_dropout=float(args.mix_dropout),
        bert_pooling=getattr(args, 'bert_pooling', 'mean'),
        # 2022 版叫 feat_pad_index；它是 BERT 词表里 [PAD] 的下标（本模型为 1）
        bert_pad_index=int(getattr(args, 'feat_pad_index', 0)),
        freeze=True,
        embed_dropout=float(args.embed_dropout),
        n_lstm_hidden=int(args.n_lstm_hidden),
        n_lstm_layers=int(args.n_lstm_layers),
        encoder_dropout=float(getattr(args, 'lstm_dropout', 0.33)),
        n_arc_mlp=int(args.n_mlp_arc),
        n_rel_mlp=int(args.n_mlp_rel),
        mlp_dropout=float(args.mlp_dropout),
        scale=0,
        pad_index=int(args.pad_index),
        unk_index=int(args.unk_index),
        device=device,
    )


def build_transform(saved_transform):
    """用 checkpoint 自带字段重建 CoNLL，补上 1.1.x 需要的 texts 占位字段。"""
    words, bert = saved_transform.FORM
    # Field/RawField 顺序决定 batch 解包顺序：words, texts, bert
    form = (words, RawField('texts'), bert)
    return CoNLL(FORM=form, HEAD=saved_transform.HEAD, DEPREL=saved_transform.DEPREL)


def load_parser(ckpt=DEFAULT_CKPT, device='cpu', verbose=True):
    state = torch.load(ckpt, map_location='cpu', weights_only=False, pickle_module=dill)
    args = state['args']

    if verbose:
        print(f'[load] checkpoint: {ckpt}')
        print(f'[load] name={state["name"]}  feat={args.feat}  bert={args.bert}')

    transform = build_transform(state['transform'])
    if verbose:
        transform.eval()
        print(f'[load] transform.fields = {transform.fields}')
        print(f'[load] flattened (eval) = {[f.name for f in transform.flattened_fields]}')
        transform.train()

    model = BiaffineDependencyModel(**build_model_kwargs(args, device))

    src = state['state_dict']
    mapped = {map_state_key(k): v for k, v in src.items()}
    missing, unexpected = model.load_state_dict(mapped, strict=False)
    if verbose:
        print(f'[load] state_dict: {len(src)} keys -> {len(mapped)} mapped')
        print(f'[load] missing({len(missing)}) = {missing}')
        print(f'[load] unexpected({len(unexpected)}) = {unexpected}')

    model.to(device).eval()

    parser_args = state['args']
    parser_args.device = device
    parser = BiaffineDependencyParser(parser_args, model, transform)
    parser.checkpoint_state_dict = None

    if verbose:
        covered = set(mapped) & set(model.state_dict().keys())
        print(f'[load] weights covered: {len(covered)}/{len(model.state_dict())} model tensors')
    return parser


def mecab_tokenize(sentence):
    """用 udkanbun 自带的 mecab-kanbun 词典分词（与 ud-kanbun 训练切分一致）。"""
    from MeCab import Tagger
    pkg = os.path.join(SITE_PACKAGES, 'udkanbun')
    r, d = os.path.join(pkg, 'mecabrc'), os.path.join(pkg, 'mecab-kanbun')
    # Windows 路径含反斜杠，MeCab 参数需要转义
    tagger = Tagger('-r ' + r.replace('\\', '\\\\') + ' -d ' + d.replace('\\', '\\\\'))
    words = []
    for line in tagger.parse(sentence).splitlines():
        if line in ('EOS', ''):
            continue
        words.append(line.split('\t')[0])
    return words


def parse_words(parser, words, verbose=True):
    dataset = parser.predict([words], lang=None, verbose=verbose)
    sentence = dataset.sentences[0]
    arcs = dataset.arcs[0]
    rels = dataset.rels[0]
    return list(words), list(arcs), list(rels)


def main():
    ap = argparse.ArgumentParser(description='guwenbert-base.supar 手写加载器 + 依存解析')
    ap.add_argument('sentence', nargs='?', default='王顧左右而言他')
    ap.add_argument('--words', nargs='+', default=None, help='显式给分词结果，跳过 MeCab')
    ap.add_argument('--ckpt', default=DEFAULT_CKPT)
    ap.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    ap.add_argument('--quiet', action='store_true')
    arg = ap.parse_args()

    verbose = not arg.quiet
    parser = load_parser(arg.ckpt, arg.device, verbose=verbose)

    words = arg.words if arg.words else mecab_tokenize(arg.sentence)
    if verbose:
        print(f'\n[input] {" ".join(words)}')

    words, arcs, rels = parse_words(parser, words, verbose=verbose)

    print('\n=== 依存解析结果 ===')
    print(f'{"ID":>3}  {"FORM":<6} {"HEAD":>4}  DEPREL')
    for i, (w, h, r) in enumerate(zip(words, arcs, rels), 1):
        print(f'{i:>3}  {w:<6} {h:>4}  {r}')

    print('\n=== 弧（head -> dep, label）===')
    for i, (w, h, r) in enumerate(zip(words, arcs, rels), 1):
        head = 'ROOT' if h == 0 else f'{h}:{words[h - 1]}'
        print(f'  {head} --{r}--> {i}:{w}')

    print('\n=== 树状 ===')
    print_tree(words, arcs, rels)
    return 0


def print_tree(words, arcs, rels):
    children = {}
    for i, h in enumerate(arcs, 1):
        children.setdefault(h, []).append(i)

    def walk(node, prefix='', last=True, label=None):
        if node == 0:
            text = 'ROOT'
        else:
            text = f'{words[node - 1]}  [{rels[node - 1]}]'
        branch = '' if node == 0 else ('└─ ' if last else '├─ ')
        print(prefix + branch + text)
        kids = children.get(node, [])
        for k, child in enumerate(kids):
            walk(child, prefix + ('' if node == 0 else ('   ' if last else '│  ')), k == len(kids) - 1)

    walk(0)
    print()


if __name__ == '__main__':
    sys.exit(main())
