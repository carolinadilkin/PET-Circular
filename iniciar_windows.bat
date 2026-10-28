@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado. Instale Python 3.11+ e tente novamente.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente Python local...
  py -m venv .venv
  if errorlevel 1 goto ERRO
)
set "PY=.venv\Scripts\python.exe"
"%PY%" -c "import streamlit,jsonschema,pandas,pypdf,openai" >nul 2>&1
if errorlevel 1 (
  echo Instalando dependencias: requer acesso a internet...
  "%PY%" -m pip install -r requirements.txt
  if errorlevel 1 goto ERRO
)
echo Iniciando PET Circular em http://127.0.0.1:8501
"%PY%" -m streamlit run app.py
exit /b 0
:ERRO
echo Nao foi possivel iniciar. Confira a mensagem acima.
pause
exit /b 1
