# REPORT_NIGHT9.md — Night 9（2026-11-18 值班段）

## 门禁判定

**门禁未过，跳过。**

依据：本夜的门禁条件是「用户给了产品推理 API 的 key / 选了哪家」。值班期间用户不在、
没有提供任何 key，也没有选择 API 供应商——按值班规则（不要自己去找 key、不要问用户要 key、
不要中途停下来等用户），本夜整夜跳过，直接执行 Night 10（前端打磨第二轮）。

## 门禁恢复后的操作清单（给用户）

1. 选定供应商后设置环境变量：`KANBUN_LLM_API_KEY`（必需）、
   `KANBUN_LLM_BASE_URL`（OpenAI 兼容端点，默认 openai）、`KANBUN_LLM_MODEL`（默认 gpt-4o-mini）。
2. 重启 uvicorn，代码路径已全部就绪：
   - 現代語訳：backend/llm.py `modern_translate()` → `MODERN_PROMPT_TEMPLATE`；
   - 語釈：`glossary()` → `GLOSSARY_PROMPT_TEMPLATE`（209 条词库命中自动作为参考）。
3. 用 10 条评测句验证质量并记录 token 成本（当日程表 Night 9 的产出）。

## 禁止事项自查

未接任何 key（不存在泄露面）；未自行注册/申请任何服务；跳过已按规则写明并提交。
