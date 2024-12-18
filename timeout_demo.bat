@echo off
echo Starting long-running process...

set "long_running_command=ping -n 61 127.0.0.1 >nul"  
set timeout_seconds=30

echo Starting command: %long_running_command%
start "" cmd /c "%long_running_command%"

timeout /t %timeout_seconds% /nobreak >nul

echo Checking if command finished...

tasklist /FI "IMAGENAME eq cmd.exe" 2>NUL | find /I /N "cmd.exe">NUL
if "%ERRORLEVEL%"=="0" (
  echo Command still running after %timeout_seconds% seconds. Terminating...
  taskkill /F /IM cmd.exe /T >nul
  echo Command terminated.
) else (
  echo Command finished within the timeout period.
)

echo Script finished.
