@echo off
rem 评测一键跑通（需后端已在 8000 运行）：基线 + 全规则 + 三份对比
setlocal
set PATH=D:\Python312;D:\Python312\Scripts;%PATH%
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."
python -X utf8 tools\run_eval.py --no-merge --no-ortho eval\night4_results_baseline.json
python -X utf8 tools\run_eval.py eval\night4_results_full_v2.json
python -X utf8 tools\eval_summary.py eval\night4_results_baseline.json eval\night4_results_full_v2.json
python -X utf8 tools\classify_errors.py eval\night4_results_baseline.json
python -X utf8 tools\classify_errors.py eval\night4_results_full_v2.json
pause
