@echo off
REM Installs the watch face on a Galaxy Watch 7 over Wi-Fi (Wireless debugging).
REM Needs adb (Android platform-tools) in PATH or in this folder.
REM Watch: Settings > Developer options > ADB debugging ON + Wireless debugging ON.
setlocal
cd /d "%~dp0"
set APK=SeikoPresageDynamic-debug.apk
if not exist "%APK%" set APK=dist\SeikoPresageDynamic-debug.apk
if not exist "%APK%" (echo APK not found next to this script & exit /b 1)
where adb >nul 2>nul || if not exist adb.exe (echo adb not found. Get platform-tools: https://developer.android.com/tools/releases/platform-tools & exit /b 1)

set /p PAIR=Pairing address shown on watch (IP:PORT, empty if already paired): 
if not "%PAIR%"=="" (
  set /p CODE=6-digit pairing code: 
  adb pair %PAIR% %CODE%
)
set /p CONN=Connect address on watch main Wireless debugging screen (IP:PORT): 
adb connect %CONN%
adb -s %CONN% install -r "%APK%"
echo.
echo Done. On the watch: long-press the watch face, swipe to the end, tap +, choose "Seiko Presage Dynamic".
endlocal
