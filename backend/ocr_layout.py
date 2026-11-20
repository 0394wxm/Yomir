# -*- coding: utf-8 -*-
"""ocr_layout.py — NIGHT43 版面几何噪音过滤：只看框位置，不看文本。

Night 42 实测（REPORT_NIGHT42.md §3）：11892692 全本导入时，页脚带的手写
書き入れ/蔵書印/书志短行被识别成行混进白文（「晴辰」「筒城君」「一四十一冊」
「新助麹町三丁」等），随后被 kundoku 当句子处理，污染输出。

Night 43 测量结论（tools/night43_stats.py，标注 eval/night43_labels.json）：
  * 这类噪音**不在页边**（4 个选样页 223 框的 edge 全部 ≥42px）——「页边外侧
    X%」判据无样本，不采用；
  * 噪音集中在两处几何位置：
      1) **页脚带**：正文主栏带底（最长框的 y+h）之下的矮框（h≈23-57）。
         正文列间直接衔接、不经过页脚行（「…○子曰事」+「筒城君」+「君盡禮…」
         实为「事」直接接「君盡禮」；「成事不」+「服摩忠」+「説逐事…」实为
         「成事不」直接接「説逐事」；「…哀公」+「一四十一冊」+「問社於宰我…」
         实为「哀公」直接接「問社」）→ 页脚框是插入物，滤掉不丢正文；
      2) **主栏带内的孤立窄条**：夹在主栏列缝/缺列位的矮条（h≈83-165），
         与所有主栏长框的 overlap_x < 0.9。
  * **上部头注带（主栏带之上）不滤**：印刷头注正文（h≈159-185）与手写条
    （h≈40-120）几何重合，纯几何不可分——「新助麹町三丁」「早朝堀紀州岩朝
    不福指越」本轮放弃（Night42 §3 点名 8 行滤 6 留 2）。
  * 主栏带内窄条的 h 上限 0.45×主栏中位高：正文割注（h≈271，如 p033
    「之広世領并、然此則天子之礼諸侯等承此不行之儀」）必须留下。
选样页实测：noise 60 框滤 59 漏 1（上部头注带）、body 163 框零错滤。

判据全部为框几何（x/y/w/h/vert），GT 8 页（eval/night36_ocr_lines.json 重跑）
CER 必须不变作为回归门。
"""
# 长框组：h >= MAIN_H_FRAC * h_max 且 w >= MAIN_W_FRAC * P90(vert w) 的縦框 = 正文主栏候选
#   （宽度资格防两类翻车：p003「論語序説」篇题（w=47 短列）被当噪音；p014 贯通
#    头注带的窄长条（w=21-27）混进 main 把版心顶抬进头注带）
MAIN_H_FRAC = 0.6
MAIN_W_FRAC = 0.65   # 对 P90(全部縦框 w) 的比例——窄条占多数的页 P90 仍抓大字列
# 主栏候选 < MIN_MAIN 个 → 页面没有可估计的版心（扉页/空白页），全部保留
MIN_MAIN = 3
# 页脚带：cy >= 最长主栏框的 y+h + FOOTER_MARGIN。
# margin 为负：最长列 y+h 参差 ±30px（p014 最长列 y+h=823，页脚 cy=821-828），
# 0 会漏 cy 贴着 y_max 的页脚框；-12 实测 6 页验证页页脚全滤且不碰任何保留框。
FOOTER_MARGIN = -12

# NIGHT46 上部手写长条带（见 judge_headnote_strip）。
# 起点比 body_top（主栏 y 中位数）早 STRIP_TOP_OFFSET 以上、且长过
# STRIP_H_FRAC*h_max 的縦框 = 手写批注长条。47 页实测命中 62 框，零误伤；
# 灵敏度：offset 60-150、h_frac 0.4-0.6 命中数完全不变（平台区）。
STRIP_TOP_OFFSET = 100
STRIP_H_FRAC = 0.5

# 【被否决的判据，留档防重蹈】主栏带内孤立窄条（intruded_strip）：p019/p020/p033
# 上曾抓到 6 个真噪音（当村人名平着/亥子九丁亥 等），但 p012/p017 上主栏若有
# 顶格长列（miban.y=35），头注带落入「版心内部」，判据越界误杀头注正文约 20 行
# （「或曰獣与憲通心可」「蔑強而と群諸友観体」等）。
#
# **NIGHT46 更正**：上面「miban.y=35」的前提本身是循环论证——p012/p017 的手写
# 长条被 MAIN_W_FRAC 判据误纳为主栏，`miban.y = min(主栏 y)` 才变成 35/38。
# 改用稳健量 body_top=median(主栏 y) 后，上部手写长条可由 judge_headnote_strip
# 纯几何分离（47 页命中 62 框、零误伤、与页脚带零重叠）。intruded_strip 本身
# 仍不采用（它抓的是主栏带**内部**的窄条，与上部带无关）。


def _p90(vs):
    if not vs:
        return 0.0
    s = sorted(vs)
    return s[min(len(s) - 1, int(round(0.9 * (len(s) - 1))))]


def _main_group(boxes):
    """主栏长框组（judge_layout 与 main_column_keys 共用同一判据）。

    返回 (miban or None, main_list)。主栏候选 = 縦框 且 h >= MAIN_H_FRAC*h_max
    且 w >= MAIN_W_FRAC*P90(w)。<MIN_MAIN 个 → 版心估不出。
    """
    vert = [b for b in boxes if b["h"] >= b["w"]]
    if not vert:
        return None, []
    h_max = max(b["h"] for b in vert)
    w_ref = _p90([b["w"] for b in vert])
    main = [b for b in vert if b["h"] >= MAIN_H_FRAC * h_max
            and b["w"] >= MAIN_W_FRAC * w_ref]
    if len(main) < MIN_MAIN:
        return None, []
    miban = {"x": min(b["x"] for b in main),
             "y": min(b["y"] for b in main),
             "w": max(b["x"] + b["w"] for b in main) - min(b["x"] for b in main),
             "h": max(b["y"] + b["h"] for b in main) - min(b["y"] for b in main)}
    return miban, main


def _median(vs):
    s = sorted(vs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def judge_headnote_strip(boxes, body_top=None, h_max=None):
    """NIGHT46 上部手写长条过滤。

    `judge_layout` 只处理**页脚带**；上部头注带 Night43 判为不可做，理由是
    「头注带落入版心内部」——但那个结论用的是 `miban.y = min(主栏 y)`，而
    p012/p017 的手写长条**自己就被误判为主栏**，把 miban.y 抬到 38/36。
    这是循环论证。本判据改用稳健量 `body_top = median(主栏 y)`（47 页实测
    209-256，离群长条拉不动）。

    判据（纯几何，三条件同时成立）：
      1. 縦框（h >= w）
      2. `y + STRIP_TOP_OFFSET <= body_top`  起点远高于正文上缘
      3. `h >= STRIP_H_FRAC * h_max`         足够长（排除头注短行 h≈150-180）

    判据 2 把「长条起点」和「正文列起点」分开（body_top 是主栏 y 中位数，
    至少一半主栏列起点 >= body_top，不可能早 100px）；判据 3 把「长条」和
    「头注短行」分开（头注短行起点也高，但 h 只有 150-180）。

    47 页实测：命中 62 框/18 页，全部是夹「候」「御」「様」的手写公文批注；
    被命中框 y 在 16/18 页完全早于主栏 y 最小值；与页脚带判据**零重叠**；
    GT 8 页仅命中 1 个 `}`（Night6 已记录的刊本界框行，噪音）。
    """
    if body_top is None or h_max is None:
        _miban, main = _main_group([dict(b) for b in boxes])
        if not main:
            return []
        body_top = _median([b["y"] for b in main])
        vert = [b for b in boxes if b["h"] >= b["w"]]
        h_max = max(b["h"] for b in vert)
    return [b for b in boxes
            if b["h"] >= b["w"]
            and b["y"] + STRIP_TOP_OFFSET <= body_top
            and b["h"] >= STRIP_H_FRAC * h_max]


def judge_layout(boxes, img_w=None, img_h=None):
    """NIGHT43 版面判据（纯几何）：主栏长框组 → 版心 → 页脚带过滤。

    boxes: junk3 过滤后的 LINE 框 [{x,y,w,h}, ...]
    返回: (miban or None, [(box, reason), ...])，顺序与输入一致；
          reason ∈ {None, "footer_band"}。
    img_w/img_h 留作签名占位（当前判据只用框间相对几何）。
    """
    del img_w, img_h
    miban, main = _main_group(boxes)
    if miban is None:
        return None, [(b, None) for b in boxes]
    y_max = max(b["y"] + b["h"] for b in main)
    out = []
    for b in boxes:
        cy = b["y"] + b["h"] / 2.0
        reason = None
        if b["h"] >= b["w"] and cy >= y_max + FOOTER_MARGIN:  # 只判縦框；横框一律保留
            reason = "footer_band"
        out.append((b, reason))
    return miban, out


# ---------------------------------------------------------------------------
# NIGHT45: 列单元内的并列主栏重排（阅读顺序）
#
# **Night45 的原假设被证伪**：一开始以为是「头注被 `_cluster_order` 的全局 x
# 排序切开」。用**与原型无关**的列连续性指标（tools/night45_contiguity.py）
# 按生产列定义度量：原顺序 659 列**零打断**（43/43 页每列连续），而「头注
# 归列」原型反而制造 48 处打断、31 页变差 → 该原型废弃，未进生产代码。
#
# **真缺陷**（tools/night45_maincol_order.py 的 I5）：`_cluster_order` 用
# x 重叠 ≥0.4 的**传递闭包**聚列，一个跨列的头注能把左右两个主栏桥接进同一
# 列单元；单元内部只按 y 排序，而并排两主栏的 y 只差 2px（p021: 215 vs 217），
# 先后由噪声决定 → 可能左先右后，整段正文读反。p021 实测：「天下之無道也
# 久矣、天将以夫子爲木鐸」被排成了「…木鐸」在前、「天下之無道也」在后。
#
# **修复**：只在列单元内部**重排主栏框所占的槽位**（按右缘 x 右→左），
# 非主栏框位置逐位不动。47 页实测（filter=ON 归档）：1 页顺序变化（p021），
# I5 主栏列对颠倒 2→0（另一处 p017 是手写批注被宽判据纳入主栏，不属正文），
# 置换与内容多重集不变。KANBUN_OCR_MAINCOL=0 关闭；默认开启。
MAIN_COL_OVERLAP = 0.4   # 与 _cluster_order 的列聚类阈值同值


def main_column_keys(boxes):
    """`_main_group` 判定为主栏的框的几何键集合。"""
    _miban, main = _main_group([dict(b) for b in boxes])
    return {(b["x"], b["y"], b["w"], b["h"]) for b in main}


# NIGHT49 割注并排槽重排的 y 容差（像素）。
# 同一列单元内，|Δy_top| <= 此值的连续框视为「同一个 y 槽」= 縦書き里并排的
# 半行（割注双行、并列主栏）。槽内应右→左读，而 `sorted(key=y)` 是纯 y 序，
# 两半顶端差 1-4px 就会把左半排到前面。
# 选值依据（tools/night49_tol_probe.py）：全本 536 个「单元内 x 不相交的相邻
# 框对」的 |Δy| 有 519 个 (96.8%) <= 7px，12-40px 区间几乎空——8 落在平台区。
# 敏感性（tools/night49_sweep.py）：TOL 4-30 右先率恒为 99.3%、退化恒为 0。
WARICHU_TOL = 8


def reorder_warichu_slots(items, tol=None):
    """列单元内：同一 y 槽（|Δy| <= tol）的并排框按右→左排。

    items: 已按 y 排好序的列单元框列表（`_cluster_order` 的单元内顺序）
    返回: 新列表（长度与内容多重集不变）

    为什么需要：縦書き的阅读顺序在「同一行高」上是从右到左的。原实现只按 y
    排序，y 相等或相差 1-4px 时顺序由检测框的亚像素噪声决定——实测 296 对
    严格割注里 25 对因此左右颠倒（dy(L-R) 全为 -1..-4，无一是正）。

    护栏：槽的划分只看 y（连续、以槽首框为锚，|Δy| <= tol），**不跨槽**。
    槽内所有框的 y 差值都 <= tol，几何上不可能构成「上下堆叠」关系，所以
    重排不会打乱任何真正的上下阅读顺序——上下相接的框 Δy 至少是半个行高，
    必然落在不同槽。槽内若有高度重合的重复检测框，两者位置几乎相同，
    谁先谁后对阅读无差别。
    """
    if tol is None:
        tol = WARICHU_TOL
    if len(items) < 2:
        return items
    items = sorted(items, key=lambda t: t["y"])
    out = []
    i, n = 0, len(items)
    while i < n:
        j = i + 1
        anchor_y = items[i]["y"]
        while j < n and abs(items[j]["y"] - anchor_y) <= tol:
            j += 1
        run = items[i:j]
        if len(run) > 1:
            run = sorted(run, key=lambda t: -(t["x"] + t["w"]))
        out.extend(run)
        i = j
    return out


def reorder_main_slots(items, main_keys):
    """列单元内只重排主栏框的槽位；非主栏框位置逐位不变。

    items: 已按 y 排好序的列单元框列表（`_cluster_order` 的单元内顺序）
    返回: 新列表（长度与内容多重集不变）

    只在单元内存在 **x 互不重叠** 的主栏框对时才动手——那正是「两个并列主栏
    被跨列头注桥接」的几何特征。上下堆叠的同列长框 x 必然重叠，不会触发，
    所以普通正文列（含割注、列末短行）的顺序完全不受影响。
    """
    if len(items) < 2:
        return items
    m = [b for b in items if (b["x"], b["y"], b["w"], b["h"]) in main_keys]
    if len(m) < 2:
        return items

    def disjoint(a, b):
        return a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]

    if not any(disjoint(m[i], m[j])
               for i in range(len(m)) for j in range(i + 1, len(m))):
        return items
    by_right = sorted(m, key=lambda t: -(t["x"] + t["w"]))
    if by_right == m:
        return items
    slots = [k for k, b in enumerate(items)
             if (b["x"], b["y"], b["w"], b["h"]) in main_keys]
    out = list(items)
    for slot, b in zip(slots, by_right):
        out[slot] = b
    return out
