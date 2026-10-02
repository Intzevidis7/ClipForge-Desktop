@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe py -3.12 -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ClipForgeDesktop.spec del /q ClipForgeDesktop.spec
pyinstaller --noconfirm --clean --windowed --name ClipForgeDesktop --collect-all vosk --collect-all customtkinter --add-data "models;models" clipforge_desktop.py
if errorlevel 1 goto failed
if not exist dist\ClipForgeDesktop\_internal\models\greek goto missingmodels
if not exist dist\ClipForgeDesktop\_internal\models\english goto missingmodels
 echo.
echo Build complete: dist\ClipForgeDesktop\ClipForgeDesktop.exe
pause
exit /b 0
:missingmodels
echo ERROR: models were not copied into the packaged application.
pause
exit /b 1
:failed
echo Build failed. Read the error above.
pause
exit /b 1
