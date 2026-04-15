@echo off
setlocal enabledelayedexpansion
REM bootstrap.bat — One-command setup for Salad Loom (Windows)
REM
REM Usage (fresh install, PowerShell):
REM   powershell -c "irm https://raw.githubusercontent.com/kleer001/Salad_Loom/main/bootstrap.bat -OutFile bootstrap.bat; .\bootstrap.bat"
REM
REM Usage (re-run from inside repo):
REM   bootstrap.bat

echo.
echo === Salad Loom Bootstrap ===
echo.
echo Disk space warning: This install downloads and unpacks approximately ~1 GB of data:
echo   - Python packages (spaCy, gensim, nltk, litellm, textual...)   ~750 MB
echo   - NLTK language data (tokenizer, tagger, lexicons)              ~110 MB
echo   - GloVe word vectors (glove-wiki-gigaword-50)                    ~88 MB
echo Make sure you have at least 1.5 GB of free disk space before continuing.
echo Press Ctrl-C now to cancel, or wait 5 seconds to proceed...
echo.
timeout /t 5

REM -------------------------------------------------------
REM Step 1: Check prerequisites
REM -------------------------------------------------------
echo Step 1: Checking prerequisites

where git >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('git --version') do echo [OK]   %%v
) else (
    echo [FAIL] git is not installed. Please install git first.
    echo        https://git-scm.com/download/win
    exit /b 1
)

set "PYTHON="
for %%c in (python3 python) do (
    if not defined PYTHON (
        where %%c >nul 2>&1
        if !errorlevel! equ 0 (
            for /f "tokens=*" %%v in ('%%c -c "import sys; v=sys.version_info; print(f\"{v.major}.{v.minor}\")" 2^>nul') do (
                set "py_ver=%%v"
            )
            if defined py_ver (
                for /f "tokens=1,2 delims=." %%a in ("!py_ver!") do (
                    if %%a geq 3 if %%b geq 8 (
                        set "PYTHON=%%c"
                    )
                )
            )
        )
    )
)

if defined PYTHON (
    for /f "tokens=*" %%v in ('!PYTHON! --version') do echo [OK]   %%v
) else (
    echo [FAIL] Python 3.8+ is required but not found.
    echo        https://www.python.org/downloads/
    exit /b 1
)

set "NODE_AVAILABLE=0"
where node >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1 delims=." %%v in ('node -v') do (
        set "node_major=%%v"
        set "node_major=!node_major:v=!"
    )
    if !node_major! geq 18 (
        set "NODE_AVAILABLE=1"
        for /f "tokens=*" %%v in ('node -v') do echo [OK]   Node.js %%v found — GUI mode available
    ) else (
        echo [!!]   Node.js found but 18+ recommended — GUI mode may not build
    )
) else (
    echo [!!]   Node.js not found — GUI mode unavailable (TUI/REPL/API still work^)
)

REM -------------------------------------------------------
REM Step 2: Clone repo (skip if already inside it)
REM -------------------------------------------------------
echo.
echo Step 2: Repository

if exist "salad_loom" if exist "requirements.txt" if exist "src\core" (
    echo [OK]   Already inside Salad Loom repo — skipping clone
    goto :skip_clone
)

echo [..]   Cloning Salad_Loom...
git clone https://github.com/kleer001/Salad_Loom.git
cd Salad_Loom
echo [OK]   Cloned into %cd%

:skip_clone
set "REPO_DIR=%cd%"

REM -------------------------------------------------------
REM Step 3: Python environment
REM -------------------------------------------------------
echo.
echo Step 3: Python environment

if not exist ".venv" (
    echo [..]   Creating virtual environment...
    !PYTHON! -m venv .venv
)
echo [OK]   Virtual environment: .venv\

call .venv\Scripts\activate.bat
set "PYTHON=python"

echo [..]   Installing Python dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
python -m pip install -e . --quiet
echo [OK]   Python dependencies installed

REM -------------------------------------------------------
REM Step 4: NLP models
REM -------------------------------------------------------
echo.
echo Step 4: NLP models

echo [..]   Downloading spaCy English model...
python -m spacy download en_core_web_sm --quiet
echo [OK]   spaCy en_core_web_sm installed

echo [..]   Downloading NLTK data...
python -c "import nltk; [nltk.download(p, quiet=True) for p in ['averaged_perceptron_tagger_eng','punkt_tab','words','cmudict']]"
echo [OK]   NLTK data downloaded

if exist "data\models\glove-wiki-gigaword-50.kv" (
    echo [OK]   GloVe word vectors already present — skipping download
) else (
    echo [..]   Downloading GloVe word vectors (~88 MB, one-time^) ...
    if not exist "data\models" mkdir data\models
    python -c "import gensim.downloader as api, pathlib; wv=api.load('glove-wiki-gigaword-50'); wv.save('data/models/glove-wiki-gigaword-50.kv'); print('  Saved.')"
    echo [OK]   GloVe vectors saved to data\models\
)

REM -------------------------------------------------------
REM Step 5: GUI (optional)
REM -------------------------------------------------------
echo.
echo Step 5: Web GUI (optional^)

if %NODE_AVAILABLE% equ 1 (
    echo [..]   Installing GUI dependencies...
    cd src\GUI
    call npm install --silent
    echo [..]   Building GUI...
    call npm run build --silent
    cd "%REPO_DIR%"
    echo [OK]   GUI built — launch with: salad_loom -g
) else (
    echo [!!]   Skipping GUI build (Node.js not available^)
    echo        Install Node.js 18+ then re-run this script to enable GUI mode
)

REM -------------------------------------------------------
REM Step 6: MCP client configuration
REM -------------------------------------------------------
echo.
echo Step 6: MCP client configuration

set "HAVE_CLAUDE_CODE=0"
set "HAVE_CLAUDE_DESKTOP=0"

where claude >nul 2>&1
if !errorlevel! equ 0 (
    set "HAVE_CLAUDE_CODE=1"
    echo [OK]   Claude Code CLI detected
)

set "DESKTOP_CONFIG=%APPDATA%\Claude\claude_desktop_config.json"
if exist "%LOCALAPPDATA%\Programs\claude-desktop" set "HAVE_CLAUDE_DESKTOP=1"
if exist "%APPDATA%\Claude" set "HAVE_CLAUDE_DESKTOP=1"
if !HAVE_CLAUDE_DESKTOP! equ 1 echo [OK]   Claude Desktop detected

set "VENV_PYTHON=%REPO_DIR%\.venv\Scripts\python.exe"
set "MCP_SERVER=%REPO_DIR%\mcp_server"

if !HAVE_CLAUDE_CODE! equ 1 if !HAVE_CLAUDE_DESKTOP! equ 1 (
    echo.
    echo Detected both Claude Code and Claude Desktop.
    echo   1^) Claude Code  (CLI^)
    echo   2^) Claude Desktop (GUI^)
    echo   3^) Both
    set /p "MCP_CHOICE=Configure which? [1/2/3]: "
    if "!MCP_CHOICE!"=="1" goto :cfg_code_only
    if "!MCP_CHOICE!"=="2" goto :cfg_desktop_only
    if "!MCP_CHOICE!"=="3" goto :cfg_both
    echo [!!]   Invalid choice — skipping MCP configuration
    goto :cfg_done
)
if !HAVE_CLAUDE_CODE! equ 1 goto :cfg_code_only
if !HAVE_CLAUDE_DESKTOP! equ 1 goto :cfg_desktop_only

echo [!!]   Neither Claude Code nor Claude Desktop detected.
echo   Install one of:
echo     Claude Code:    https://docs.anthropic.com/en/docs/claude-code
echo     Claude Desktop: https://claude.ai/download
echo.
echo   Then re-run this script, or configure manually.
goto :cfg_done

:cfg_both
call :do_cfg_code
call :do_cfg_desktop
goto :cfg_done

:cfg_code_only
call :do_cfg_code
goto :cfg_done

:cfg_desktop_only
call :do_cfg_desktop
goto :cfg_done

:do_cfg_code
echo [..]   Configuring Claude Code MCP server...
claude mcp remove salad-loom >nul 2>&1
claude mcp add --transport stdio --scope user salad-loom -- "!VENV_PYTHON!" "!MCP_SERVER!"
echo [OK]   Claude Code configured (verify with: claude mcp list^)
goto :eof

:do_cfg_desktop
echo [..]   Configuring Claude Desktop MCP server...
python -c "import json,sys,os; cf=r'%DESKTOP_CONFIG%'; rd=r'%REPO_DIR%'; c=json.load(open(cf)) if os.path.exists(cf) else {}; c.setdefault('mcpServers',{})['salad-loom']={'command':os.path.join(rd,'.venv','Scripts','python.exe'),'args':[os.path.join(rd,'mcp_server')]}; os.makedirs(os.path.dirname(cf),exist_ok=True); f=open(cf,'w'); json.dump(c,f,indent=2); f.write('\n'); f.close()"
echo [OK]   Claude Desktop configured: %DESKTOP_CONFIG%
goto :eof

:cfg_done

REM -------------------------------------------------------
REM Done
REM -------------------------------------------------------
echo.
echo === Salad Loom is ready! ===
echo   Repo:   %REPO_DIR%
echo   Venv:   %REPO_DIR%\.venv\
echo.
echo   Launch modes (activate venv first: .venv\Scripts\activate^):
echo     salad_loom -t     Terminal UI
echo     salad_loom -r     Python REPL
echo     salad_loom -a     API server  (http://localhost:8000/api/v1/docs^)
if %NODE_AVAILABLE% equ 1 (
    echo     salad_loom -g     Web GUI     (http://localhost:5173^)
)
echo     salad_loom -b -f examples\recipes\n_plus_7.json   Batch mode
echo.
echo   Try a recipe: salad_loom -b -f examples\recipes\the_full_salad.json
echo.
