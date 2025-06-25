@echo off
echo ====================================================
echo   Sistema de Monitoramento Inteligente de Precos
echo ====================================================
echo.
echo Iniciando servidor web...
echo.
echo Aguarde um momento enquanto o sistema inicia...
echo O navegador sera aberto automaticamente em instantes.
echo.
echo Para encerrar o servidor, pressione CTRL+C nesta janela.
echo ====================================================
echo.

REM Verificar se o Python está instalado
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Python nao encontrado! Verifique se o Python esta instalado.
    pause
    exit /b
)

REM Verificar se os pacotes necessários estão instalados
echo Verificando dependencias...
python -m pip install -r requirements.txt

REM Criar diretórios necessários se não existirem
if not exist "static\css" mkdir "static\css"
if not exist "static\js" mkdir "static\js" 
if not exist "templates" mkdir "templates"
if not exist "resultados" mkdir "resultados"

REM Iniciar o servidor web e abrir o navegador automaticamente
start http://localhost:5000
python app.py

pause
