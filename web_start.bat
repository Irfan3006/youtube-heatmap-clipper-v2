@echo off
title YouTube Heatmap Clipper

cd /d "E:\File_IRFAN\CODE\youtube-heatmap-clipper"

echo Starting server...
start "Python Server" cmd /k python webapp.py

timeout /t 5 /nobreak >nul

start http://127.0.0.1:5000

exit