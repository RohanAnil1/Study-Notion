@echo off
:: ============================================
:: Install Study-Notion as a Windows Service
:: Run this script AS ADMINISTRATOR
:: ============================================

:: Download NSSM first: https://nssm.cc/download
:: Extract nssm.exe to a permanent location and update the path below:
set NSSM_PATH=C:\nssm\nssm.exe
set SERVICE_NAME=StudyNotion
set PYTHON_EXE=D:\GITHUB PROJECTS\Study-Notion-main\.venv\Scripts\python.exe
set APP_DIR=D:\GITHUB PROJECTS\Study-Notion-main\Study-Notion-main

echo Installing Study-Notion as Windows Service...

:: Remove existing service if any
%NSSM_PATH% stop %SERVICE_NAME% >nul 2>&1
%NSSM_PATH% remove %SERVICE_NAME% confirm >nul 2>&1

:: Install the service
%NSSM_PATH% install %SERVICE_NAME% "%PYTHON_EXE%" "-c" "from main import create_app; app = create_app(); app.run(host='0.0.0.0', port=5000, debug=False)"
%NSSM_PATH% set %SERVICE_NAME% AppDirectory "%APP_DIR%"
%NSSM_PATH% set %SERVICE_NAME% DisplayName "Study-Notion LMS Server"
%NSSM_PATH% set %SERVICE_NAME% Description "Study-Notion AI-Powered Learning Platform running on port 5000"
%NSSM_PATH% set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM_PATH% set %SERVICE_NAME% AppStdout "%APP_DIR%\logs\service_stdout.log"
%NSSM_PATH% set %SERVICE_NAME% AppStderr "%APP_DIR%\logs\service_stderr.log"
%NSSM_PATH% set %SERVICE_NAME% AppRestartDelay 5000

:: Start the service
%NSSM_PATH% start %SERVICE_NAME%

echo.
echo ✅ Service installed and started!
echo    Access: http://localhost:5000
echo    Manage: services.msc → "Study-Notion LMS Server"
echo    Stop:   nssm stop StudyNotion
echo    Remove: nssm remove StudyNotion confirm
pause
