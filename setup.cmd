@echo off
python -m pip install --upgrade pip

pip install -U disnake
pip install -U matplotlib
pip3 install -U aiohttp
pip install requests
pip install battlemetrics

timeout /t 5