# AuthentiChain PowerShell Runner
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "         AuthentiChain: E-Commerce Product Authenticity Platform" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""

$PythonExe = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
if (-not (Test-Path $PythonExe)) {
    if (Test-Path "C:\Python313\python.exe") {
        $PythonExe = "C:\Python313\python.exe"
    } else {
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if ($cmd) {
            $PythonExe = $cmd.Source
        } else {
            Write-Host "[ERROR] Python 3.13 was not found on your system!" -ForegroundColor Red
            Exit
        }
    }
}

Write-Host "[INFO] Using Python: $PythonExe" -ForegroundColor Green
Write-Host ""
Write-Host "Select an option:"
Write-Host "  [1] Start Web Server and User Interface (http://localhost:8000)" -ForegroundColor Yellow
Write-Host "  [2] Run Automated Test Suite (12 Unit & Security Tests)" -ForegroundColor Yellow
Write-Host "  [3] Run Interactive CLI Demonstration" -ForegroundColor Yellow
Write-Host "  [4] Exit"
Write-Host ""

$choice = Read-Host "Enter choice [1-4] (Default is 1)"
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

switch ($choice) {
    "1" {
        Write-Host "`n[INFO] Starting Web Server at http://localhost:8000 ..." -ForegroundColor Cyan
        Start-Process "http://localhost:8000"
        & $PythonExe server.py
    }
    "2" {
        Write-Host "`n[INFO] Running Blockchain Unit & Security Test Suite ..." -ForegroundColor Cyan
        & $PythonExe -m unittest tests/test_blockchain.py -v
    }
    "3" {
        Write-Host "`n[INFO] Running Interactive CLI Demonstration ..." -ForegroundColor Cyan
        & $PythonExe demo_cli.py
    }
    Default {
        Write-Host "Exiting."
    }
}
