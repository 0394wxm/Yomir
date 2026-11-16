# -*- coding: utf-8 -*-
"""
llm.py — 現代語訳 / 語釈 的 LLM 适配层（Night 2，只搭架子，不接 key）。

约定:
- 绝不在代码/配置里写死任何 API key 或 token；也绝不从 ZCode 抓 token。
- key 由用户以后通过环境变量单独提供，本模块只读变量名：
    KANBUN_LLM_API_KEY   必需。没有它 → mock 模式。
    KANBUN_LLM_BASE_URL  可选。OpenAI 兼容 /chat/completions 的 base url。
    KANBUN_LLM_MODEL     可选。模型名。
- mock 模式（默认）返回占位字符串，字段结构与现代語訳/語釈上线后一致：
    modern   : str
    glossary : list[ {word: str, reading: str, meaning: str} ]

TODO(等用户提供 key 后):
  modern_translate() 换成真实调用（OpenAI 兼容 chat/completions，一次请求带
  白文+書き下し文，要求返回现代日语译文）；glossary() 要求返回 JSON 数组。
"""
import json
import os

MODERN_PLACEHOLDER = "待接入 LLM（占位）"


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
    # TODO(用户给 key 后启用): 下面是真实调用路径，先搭好架子不启用。
    try:
        prompt = (
            "次の漢文の書き下し文を現代日本語に訳してください。出力は訳文のみ。\n\n"
            "白文: %s\n書き下し文:\n%s" % (hakubun, kakikudashi)
        )
        return _chat([{"role": "user", "content": prompt}]).strip()
    except Exception as e:
        return "LLM 调用失败: %r" % (e,)


def glossary(hakubun: str) -> list:
    """語釈。无 key 时走离线 mock，返回空列表（前端显示占位）。"""
    if not _has_key():
        return []
    # TODO(用户给 key 后启用): 要求模型返回 [{"word","reading","meaning"}] JSON。
    try:
        prompt = (
            "次の漢文の白文から、訓読上学習者向けに重要な語 5 語程度を選び、"
            "JSON配列 [{\"word\",\"reading\",\"meaning\"}] として出力してください。JSONのみ。\n\n白文: %s" % hakubun
        )
        content = _chat([{"role": "user", "content": prompt}]).strip()
        return json.loads(content)
    except Exception as e:
        return [{"word": "(LLM 调用失败)", "reading": "", "meaning": repr(e)}]
