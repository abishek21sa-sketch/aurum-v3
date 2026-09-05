@echo off
setlocal EnableExtensions
cd /d "%~dp0AURUM"
call scripts\product_bootstrap.cmd
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe scripts\product_runtime.py --serve
exit /b %errorlevel%
