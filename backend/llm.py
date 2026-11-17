# -*- coding: utf-8 -*-
"""
llm.py — 現代語訳 / 語釈 的 LLM 适配层（Night 2 建骨架 / Night 8 提示词+词库）。

约定:
- 绝不在代码/配置里写死任何 API key 或 token；也绝不从 ZCode 抓 token。
- key 由用户以后通过环境变量单独提供，本模块只读变量名：
    KANBUN_LLM_API_KEY   必需。没有它 → 离线模式（語釈走词库 / modern 留占位）。
    KANBUN_LLM_BASE_URL  可选。OpenAI 兼容 /chat/completions 的 base url。
    KANBUN_LLM_MODEL     可选。模型名。
- Night 8: 提示词模板正式化（MODERN_PROMPT_TEMPLATE / GLOSSARY_PROMPT_TEMPLATE），
  glossary 无 key 时改从 backend/glossary_lexicon.py 的 209 条文语词库查询。

TODO(等用户提供 key 后):
  modern_translate() 换成真实调用（OpenAI 兼容 chat/completions，一次请求带
  白文+書き下し文，要求返回现代日语译文）；glossary() 用 GLOSSARY_PROMPT_TEMPLATE
  要求返回 JSON 数组，并把词库命中作为 few-shot 参考。
"""
import json
import os

from backend.glossary_lexicon import LEXICON_SOURCE, find_in_lexicon

MODERN_PLACEHOLDER = "待接入 LLM（占位）"

# NIGHT8: 現代語訳 提示词模板（key 配置后 _chat 调用使用）
MODERN_PROMPT_TEMPLATE = (
    "あなたは漢文教育の専門家です。次の漢文の白文と書き下し文を、"
    "現代日本語の自然な文に翻訳してください。\n"
    "要件:\n"
    "1. 訓読に依拠しつつ、現代語として自然な文にすること。\n"
    "2. 固有名詞・数詞は原文の漢字を保つこと。\n"
    "3. 出力は訳文のみ（前後に説明を付けない）。\n"
    "4. 原文が複数文の場合は、文の順序を保って訳す。\n\n"
    "白文:\n{hakubun}\n\n書き下し文:\n{kakikudashi}"
)

# NIGHT8: 語釈 提示词模板（词库命中を参考情報として添付）
GLOSSARY_PROMPT_TEMPLATE = (
    "あなたは漢文教育の専門家です。次の漢文の白文から、初学者向けに重要な語"
    "5語程度を選び、語釈を作ってください。\n"
    "要件:\n"
    "1. 出力は JSON 配列のみ: [{{\"word\":\"…\",\"reading\":\"…\",\"meaning\":\"…\"}}]\n"
    "2. reading は現代仮名遣い。\n"
    "3. meaning は50字以内の簡明な説明（出典の故事成語の場合は故事名を添える）。\n"
    "4. 次の词库ヒットは参考にできる（そのまま採用してもよい）:\n{lexicon_hits}\n\n"
    "白文:\n{hakubun}\n\n書き下し文:\n{kakikudashi}"
)


def _has_key() -> bool:
    return bool(os.environ.get("KANBUN_LLM_API_KEY"))


def _chat(messages, timeout=60):
    """OpenAI 兼容 /chat/completions 调用。key 只从环境变量读。"""
    import urllib.request

    base = os.environ.get("KANBUN_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("KANBUN_LLM_MODEL", "gpt-4o-mini")
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps({"model": model, "messages": messages, "temperature": 0.2}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ["KANBUN_LLM_API_KEY"],
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def modern_translate(hakubun: str, kakikudashi: str) -> str:
    """現代語訳。无 key 时走离线 mock，返回占位字符串。"""
    if not _has_key():
        return MODERN_PLACEHOLDER
    # TODO(用户给 key 后启用): 提示词见 MODERN_PROMPT_TEMPLATE。
    try:
        prompt = MODERN_PROMPT_TEMPLATE.format(hakubun=hakubun, kakikudashi=kakikudashi)
        return _chat([{"role": "user", "content": prompt}]).strip()
    except Exception as e:
        return "LLM 调用失败: %r" % (e,)


def glossary(hakubun: str, kakikudashi: str = "") -> list:
    """語釈。Night 8: 无 key 时先查 209 条文语词库；查不到再留空。

    词库来源与未校对声明见 backend/glossary_lexicon.py 头部注释。
    有 key 时（TODO 启用）走 GLOSSARY_PROMPT_TEMPLATE，把词库命中作为参考。
    """
    if not _has_key():
        # 离线模式: 词库优先（最多 5 条），词库没有命中就留空数组
        hits = find_in_lexicon((hakubun or "") + " " + (kakikudashi or ""), max_hits=5)
        return hits
    # TODO(用户给 key 后启用): 提示词见 GLOSSARY_PROMPT_TEMPLATE。
    try:
        hits = find_in_lexicon((hakubun or "") + " " + (kakikudashi or ""), max_hits=5)
        lexicon_lines = "\n".join(
            "- {w}（{r}）: {m}".format(w=h["word"], r=h["reading"], m=h["meaning"]) for h in hits
        ) or "（なし）"
        prompt = GLOSSARY_PROMPT_TEMPLATE.format(
            hakubun=hakubun, kakikudashi=kakikudashi, lexicon_hits=lexicon_lines)
        content = _chat([{"role": "user", "content": prompt}]).strip()
        return json.loads(content)
    except Exception as e:
        return [{"word": "(LLM 调用失败)", "reading": "", "meaning": repr(e), "source": "llm-error"}]
