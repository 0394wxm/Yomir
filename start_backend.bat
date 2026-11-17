@echo off
rem kanbun-kakikudashi 后端一键启动（双击运行）
rem 需要已解压 OCR 运行目录（见 README），否則 OCR 不可用、文本訓読照常。
setlocal
set PATH=D:\Python312;D:\Python312\Scripts;%PATH%
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo [kanbun] backend starting on http://127.0.0.1:8000 ...
python -X utf8 -m uvicorn backend.main:app --port 8000 --host 127.0.0.1
pause
