@echo off
title Study-Notion Server
cd /d "D:\GITHUB PROJECTS\Study-Notion-main\Study-Notion-main"
echo Starting Study-Notion server...
echo Server will be available at http://127.0.0.1:5000
echo Press Ctrl+C to stop.
echo.

:loop
"D:\GITHUB PROJECTS\Study-Notion-main\.venv\Scripts\python.exe" -c "from main import create_app; app = create_app(); app.run(host='0.0.0.0', port=5000, debug=False)"
echo.
echo Server crashed or stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
