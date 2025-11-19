@echo off@echo off@echo off

chcp 65001 >nul

title Criador de Shorts Virais - Inicializadorchcp 65001 >nulecho ============================================



echo.title Criador de Shorts Virais - Inicializadorecho   INICIANDO CRIADOR DE SHORTS VIRAIS

echo ============================================================

echo 🚀 CRIADOR DE SHORTS VIRAISecho ============================================

echo ============================================================

echo.echo.echo.

echo 📦 Iniciando servidores...

echo.echo ============================================================



REM Verificar se o Ollama está rodandoecho 🚀 CRIADOR DE SHORTS VIRAISREM Verifica se o Ollama está rodando

echo [1/4] 🤖 Verificando Ollama...

tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NULecho ============================================================echo [1/3] Verificando Ollama...

if "%ERRORLEVEL%"=="0" (

    echo       ✅ Ollama já está rodando!echo.tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL

) else (

    echo       ⏳ Iniciando Ollama...echo 📦 Iniciando servidores...if "%ERRORLEVEL%"=="0" (

    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve

    timeout /t 3 /nobreak >nulecho.    echo      Ollama ja esta rodando!

    echo       ✅ Ollama iniciado!

)) else (



REM Verificar se o ambiente virtual existeREM Verificar se o Ollama está rodando    echo      Iniciando Ollama...

echo.

echo [2/4] 🐍 Verificando ambiente Python...echo [1/4] 🤖 Verificando Ollama...    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve

if not exist "backend\venv\" (

    echo       ❌ Ambiente virtual não encontrado!tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL    timeout /t 3 >nul

    echo          Execute na pasta backend: python -m venv venv

    pauseif "%ERRORLEVEL%"=="0" ()

    exit /b 1

)    echo       ✅ Ollama já está rodando!

echo       ✅ Ambiente virtual encontrado!

) else (echo.

REM Iniciar backend

echo.    echo       ⏳ Iniciando Ollama...echo [2/3] Iniciando Backend Flask...

echo [3/4] 🔧 Iniciando Backend (Flask + IA)...

cd /d "%~dp0"    start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" servecd /d "%~dp0"

start "Backend - Flask + IA" cmd /k "cd backend && .\venv\Scripts\activate && python app.py"

timeout /t 3 /nobreak >nul    timeout /t 3 /nobreak >nulstart "Backend - Criador de Shorts" cmd /k "call venv\Scripts\activate && python run.py"

echo       ✅ Backend iniciado!

    echo       ✅ Ollama iniciado!timeout /t 3 >nul

REM Iniciar frontend

echo.)

echo [4/4] ⚛️  Iniciando Frontend (React + TypeScript)...

start "Frontend - React" cmd /k "cd frontend-new && npm run dev"echo.

timeout /t 5 /nobreak >nul

echo       ✅ Frontend iniciado!REM Verificar se o ambiente virtual existeecho [3/3] Abrindo Interface Web...



REM Abrir navegadorecho.start "" "%~dp0frontend\index.html"

echo.

echo 🌐 Abrindo navegador...echo [2/4] 🐍 Verificando ambiente Python...

timeout /t 2 /nobreak >nul

start http://localhost:5174if not exist "venv\" (echo.



echo.    echo       ❌ Ambiente virtual não encontrado!echo ============================================

echo ============================================================

echo ✅ TODOS OS SERVIÇOS INICIADOS COM SUCESSO!    echo          Execute: python -m venv venvecho   TUDO PRONTO!

echo ============================================================

echo.    pauseecho ============================================

echo 📍 URLs Disponíveis:

echo    🎨 Frontend: http://localhost:5173    exit /b 1echo.

echo    🔌 Backend:  http://localhost:5000

echo    🤖 Ollama:   http://localhost:11434)echo Backend: http://localhost:5000

echo.

echo 💡 Dicas:echo       ✅ Ambiente virtual encontrado!echo Frontend: Aberto no navegador

echo    - Use Ctrl+C nos terminais para parar os servidores

echo    - Feche esta janela quando terminarecho Ollama: Rodando em background

echo    - Os dados ficam em backend/uploads e backend/outputs

echo    - Ambiente virtual em backend/venvREM Iniciar backendecho.

echo    - Variáveis de ambiente em backend/.env

echo.echo.echo Pressione qualquer tecla para fechar esta janela...

echo ============================================================

echo.echo [3/4] 🔧 Iniciando Backend (Flask + IA)...pause >nul

pause

cd /d "%~dp0"
start "Backend - Flask + IA" cmd /k "cd backend && ..\venv\Scripts\activate && python app.py"
timeout /t 3 /nobreak >nul
echo       ✅ Backend iniciado!

REM Iniciar frontend
echo.
echo [4/4] ⚛️  Iniciando Frontend (React + TypeScript)...
start "Frontend - React" cmd /k "cd frontend-new && npm run dev"
timeout /t 5 /nobreak >nul
echo       ✅ Frontend iniciado!

REM Abrir navegador
echo.
echo 🌐 Abrindo navegador...
timeout /t 2 /nobreak >nul
start http://localhost:5174

echo.
echo ============================================================
echo ✅ TODOS OS SERVIÇOS INICIADOS COM SUCESSO!
echo ============================================================
echo.
echo 📍 URLs Disponíveis:
echo    🎨 Frontend: http://localhost:5174
echo    🔌 Backend:  http://localhost:5000
echo    🤖 Ollama:   http://localhost:11434
echo.
echo 💡 Dicas:
echo    - Use Ctrl+C nos terminais para parar os servidores
echo    - Feche esta janela quando terminar
echo    - Os dados ficam em backend/uploads e backend/outputs
echo.
echo ============================================================
echo.
pause
