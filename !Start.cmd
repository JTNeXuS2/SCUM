@echo off
chcp 65001>nul
mode con:cols=70 lines=8

title "SCUM_bot %~dp0"

:start
python %~dp0SCUM_bot.py
timeout /t 5
goto start
