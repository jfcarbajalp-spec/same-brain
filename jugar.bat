@echo off
chcp 65001 >nul
title Same Brain
cd /d "%~dp0"

set PY=

where python >nul 2>nul && set PY=python
if "%PY%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if "%PY%"=="" where py >nul 2>nul && set PY=py

if "%PY%"=="" (
  echo No se ha encontrado Python. Instalalo desde https://python.org y vuelve a intentarlo.
  pause
  exit /b 1
)

%PY% server.py %1
pause
