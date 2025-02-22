@echo off
setlocal

rem Set workspace
set "WORKSPACE=%~dp0"
set "WORKSPACE=%WORKSPACE:~0,-1%"
echo Setting up Reading List Tracker...
echo Workspace: %WORKSPACE%

rem Create and update .env file
if not exist "%WORKSPACE%\config\.env" (
    copy "%WORKSPACE%\config\.env.example" "%WORKSPACE%\config\.env"
    echo WORKSPACE="%WORKSPACE%" >> "%WORKSPACE%\config\.env"
    echo Created and configured config\.env
)

rem Create virtual environment
echo Creating virtual environment...
python -m venv venv

rem Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

rem Install dependencies
echo Installing dependencies...
pip install -e .

rem Create necessary directories
echo Creating project directories...
mkdir "%WORKSPACE%\config" 2>nul
mkdir "%WORKSPACE%\templates\excel" 2>nul
mkdir "%WORKSPACE%\templates\email" 2>nul
mkdir "%WORKSPACE%\docs\images" 2>nul
mkdir "%WORKSPACE%\data\db" 2>nul
mkdir "%WORKSPACE%\data\csv" 2>nul
mkdir "%WORKSPACE%\data\backups" 2>nul
mkdir "%WORKSPACE%\data\examples" 2>nul
mkdir "%WORKSPACE%\logs" 2>nul
mkdir "%WORKSPACE%\src\migrations" 2>nul

rem Create .gitkeep files
type nul > "%WORKSPACE%\data\db\.gitkeep"
type nul > "%WORKSPACE%\data\csv\.gitkeep"
type nul > "%WORKSPACE%\data\backups\.gitkeep"
type nul > "%WORKSPACE%\logs\.gitkeep"

rem Run tests
echo Running test suite...
python -m pytest tests/

echo Setup complete!
echo To activate the virtual environment:
echo   venv\Scripts\activate

endlocal
