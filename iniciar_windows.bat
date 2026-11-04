@echo off
setlocal
cd /d "%~dp0"
echo.
echo PET Circular v0.4 Web - Interface aprovada
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PY=py"
) else (
    set "PY=python"
)
if not exist ".venv\Scripts\python.exe" (
    echo Preparando ambiente local Python...
    %PY% -m venv .venv
    if errorlevel 1 goto :error
)
echo Instalando/atualizando dependencias da interface web...
".venv\Scripts\python.exe" -m pip install -r requirements-web.txt
if errorlevel 1 goto :error
echo.
echo Abrindo PET Circular em http://127.0.0.1:8501
".venv\Scripts\python.exe" server.py
if errorlevel 1 goto :error
exit /b 0
:error
echo.
echo Falha ao iniciar. Confira o Python e a conexao com a internet.
pause
exit /b 1
