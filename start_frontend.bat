@echo off
rem kanbun-kakikudashi 前端一键启动（双击运行）
setlocal
set PATH=D:\nodejs;%PATH%
cd /d "%~dp0frontend"
echo [kanbun] frontend starting on http://localhost:5173/ ...
call npm run dev
pause
