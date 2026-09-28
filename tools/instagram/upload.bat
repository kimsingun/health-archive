@echo off
chcp 65001 > nul
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
python upload_blog_images.py "C:\Users\kimsi\OneDrive\바탕 화면\네이버블로그" %*
pause
