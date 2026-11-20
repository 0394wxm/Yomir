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

# 【被否决的判据，留档防重蹈】主栏带内孤立窄条（intruded_strip）：p019/p020/p033
# 上曾抓到 6 个真噪音（当村人名平着/亥子九丁亥 等），但 p012/p017 上主栏若有
# 顶格长列（miban.y=35），头注带落入「版心内部」，判据越界误杀头注正文约 20 行
# （「或曰獣与憲通心可」「蔑強而と群諸友観体」等）。版心 y 估计在版式多样性下
# 不可靠 → 按零错滤硬门砍掉。上部头注带（印刷头注与手写条几何重合）同样不滤。


def _p90(vs):
    if not vs:
        return 0.0
    s = sorted(vs)
    return s[min(len(s) - 1, int(round(0.9 * (len(s) - 1))))]


def judge_layout(boxes, img_w=None, img_h=None):
    """NIGHT43 版面判据（纯几何）：主栏长框组 → 版心 → 页脚带过滤。

    boxes: junk3 过滤后的 LINE 框 [{x,y,w,h}, ...]
    返回: (miban or None, [(box, reason), ...])，顺序与输入一致；
          reason ∈ {None, "footer_band"}。
    img_w/img_h 留作签名占位（当前判据只用框间相对几何）。
    """
    del img_w, img_h
    vert = [b for b in boxes if b["h"] >= b["w"]]
    if not vert:
        return None, [(b, None) for b in boxes]
    h_max = max(b["h"] for b in vert)
    w_ref = _p90([b["w"] for b in vert])
    main = [b for b in vert if b["h"] >= MAIN_H_FRAC * h_max
            and b["w"] >= MAIN_W_FRAC * w_ref]
    if len(main) < MIN_MAIN:
        return None, [(b, None) for b in boxes]
    miban = {"x": min(b["x"] for b in main),
             "y": min(b["y"] for b in main),
             "w": max(b["x"] + b["w"] for b in main) - min(b["x"] for b in main),
             "h": max(b["y"] + b["h"] for b in main) - min(b["y"] for b in main)}
    y_max = max(b["y"] + b["h"] for b in main)
    out = []
    for b in boxes:
        cy = b["y"] + b["h"] / 2.0
        reason = None
        if b["h"] >= b["w"] and cy >= y_max + FOOTER_MARGIN:  # 只判縦框；横框一律保留
            reason = "footer_band"
        out.append((b, reason))
    return miban, out
