@echo off
REM Launch the Redkeep UI (local control panel) and open it in the browser.
REM Stops when you close this window - nothing is left running.
cd /d "%~dp0"
where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python ui\server.py %*
) else (
  py ui\server.py %*
)
