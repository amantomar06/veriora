@echo off
title AuthentiChain - E-Commerce Product Authenticity Blockchain
setlocal enabledelayedexpansion

echo =======================================================================
echo          AuthentiChain: E-Commerce Product Authenticity Platform
echo =======================================================================
echo.

:: Detect Python executable
set PYTHON_CMD=
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>nul
    if !errorlevel! equ 0 (
        set PYTHON_CMD=py
    ) else (
        if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
            set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        ) else (
            echo [ERROR] Python was not found in PATH or standard installation directory!
            pause
            exit /b 1
        )
    )
)

echo [INFO] Using Python: %PYTHON_CMD%
echo.
echo Select an option:
echo   [1] Start Web Server and User Interface (http://localhost:8000)
echo   [2] Run Automated Test Suite (12 Unit & Security Tests)
echo   [3] Run Interactive CLI Demonstration
echo   [4] Exit
echo.
set /p opt="Enter choice [1-4] (Default is 1): "

if "%opt%"=="" set opt=1
if "%opt%"=="1" (
    echo [INFO] Starting Web Server at http://localhost:8000 ...
    start "" http://localhost:8000
    %PYTHON_CMD% server.py
) else if "%opt%"=="2" (
    echo [INFO] Running Blockchain Unit and Security Test Suite ...
    %PYTHON_CMD% -m unittest tests/test_blockchain.py -v
    pause
) else if "%opt%"=="3" (
    echo [INFO] Launching CLI Demonstration ...
    %PYTHON_CMD% demo_cli.py
    pause
) else (
    exit /b 0
)
