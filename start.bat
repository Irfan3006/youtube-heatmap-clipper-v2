@echo off
setlocal

cd /d "%~dp0"

title YouTube Heatmap Clipper Launcher
cls

echo ===================================================
echo   YouTube Heatmap Clipper - Auto Launcher
echo ===================================================
echo(

set "VENV_DIR=venv"
set "PYTHON_CMD="

if not exist "%VENV_DIR%\Scripts\python.exe" goto :CREATE_VENV

set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"
"%PYTHON_CMD%" -m pip --version >nul 2>&1
if not errorlevel 1 goto :DEPS

echo [WARN] Virtual environment ditemukan tetapi pip bermasalah.
echo [*] Memperbaiki virtual environment yang rusak...
rmdir /s /q "%VENV_DIR%" >nul 2>&1
set "PYTHON_CMD="

:CREATE_VENV
echo [*] Mempersiapkan Virtual Environment baru dengan Python...

py -3.11 --version >nul 2>&1
if errorlevel 1 goto :TRY_PY3
echo [OK] Python 3.11 ditemukan. Membuat venv...
py -3.11 -m venv "%VENV_DIR%"
goto :CHECK_VENV

:TRY_PY3
py -3 --version >nul 2>&1
if errorlevel 1 goto :TRY_PYTHON
echo [OK] Python 3 (py launcher) ditemukan. Membuat venv...
py -3 -m venv "%VENV_DIR%"
goto :CHECK_VENV

:TRY_PYTHON
python --version >nul 2>&1
if errorlevel 1 goto :NO_PY
echo [OK] Python system ditemukan. Membuat venv...
python -m venv "%VENV_DIR%"
goto :CHECK_VENV

:CHECK_VENV
if exist "%VENV_DIR%\Scripts\python.exe" goto :VENV_SUCCESS
goto :VENV_FAIL

:VENV_SUCCESS
set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"
"%PYTHON_CMD%" -m pip --version >nul 2>&1
if errorlevel 1 "%PYTHON_CMD%" -m ensurepip --default-pip >nul 2>&1
echo [OK] Venv berhasil dibuat.
goto :DEPS

:DEPS
echo(
echo [*] Checking ^& Installing dependencies...
"%PYTHON_CMD%" -m pip install --upgrade pip >nul 2>&1
"%PYTHON_CMD%" -m pip install -r requirements.txt
if errorlevel 1 goto :REQ_FAIL

echo [*] Checking AI Subtitle dependencies (faster-whisper)...
"%PYTHON_CMD%" -c "import faster_whisper" >nul 2>&1
if errorlevel 1 goto :INSTALL_FWHISPER
echo [OK] faster-whisper already installed.
goto :RUN

:INSTALL_FWHISPER
echo [*] Installing faster-whisper...
"%PYTHON_CMD%" -m pip install faster-whisper
if errorlevel 1 (
    echo [WARN] Gagal install faster-whisper. Fitur subtitle mungkin tidak jalan.
    echo        (Biasanya karena versi Python tidak kompatibel/preview version^)
) else (
    echo [OK] faster-whisper installed.
)

:RUN
echo(
echo ===================================================
echo   PENTING:
echo   Pastikan FFmpeg sudah terinstall agar fungsi crop jalan.
echo   Jika belum, install manual via PowerShell (Administrator^):
echo       winget install Gyan.FFmpeg
echo.
echo   Semua siap! Menjalankan Web App...
echo   Membuka browser di: http://127.0.0.1:5000
echo ===================================================
echo(

if defined YHC_CHECK_ONLY goto :DONE

start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"
"%PYTHON_CMD%" webapp.py
goto :DONE

:NO_PY
echo(
echo ===================================================
echo [!] Python tidak ditemukan di sistem Anda!
echo [*] Memulai proses download ^& instalasi otomatis Python 3.11...
echo ===================================================
echo(

set "PY_INSTALLER=%TEMP%\python-3.11.9-amd64.exe"

echo [*] Mengunduh installer Python 3.11 dari python.org...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%PY_INSTALLER%'"

if not exist "%PY_INSTALLER%" (
    echo [X] Gagal mengunduh installer Python 3.11.
    echo     Silakan unduh dan install Python 3.11 secara manual dari https://www.python.org/
    goto :FAIL
)

echo [OK] Installer berhasil diunduh.
echo [*] Menginstall Python 3.11 secara otomatis (mohon tunggu)...

"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 SimpleInstall=1
del "%PY_INSTALLER%" >nul 2>&1

:: Perbarui PATH untuk sesi CMD saat ini
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%LOCALAPPDATA%\Programs\Python\Launcher;C:\Program Files\Python311;C:\Program Files\Python311\Scripts;%PATH%"

echo [*] Memeriksa kembali Python...

py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    echo [OK] Python 3.11 berhasil terinstall.
    py -3.11 -m venv "%VENV_DIR%"
    goto :CHECK_VENV
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    echo [OK] Python 3.11 terinstall di %LOCALAPPDATA%\Programs\Python\Python311.
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -m venv "%VENV_DIR%"
    goto :CHECK_VENV
)

python --version >nul 2>&1
if not errorlevel 1 (
    echo [OK] Python terinstall.
    python -m venv "%VENV_DIR%"
    goto :CHECK_VENV
)

echo [X] Gagal mendeteksi Python secara otomatis setelah instalasi.
echo     Silakan restart jendela CMD ini dan jalankan start.bat kembali.
goto :FAIL

:VENV_FAIL
echo [X] Gagal membuat venv.
goto :FAIL

:REQ_FAIL
echo [X] Gagal install basic dependencies. Cek koneksi internet.
goto :FAIL

:FAIL
echo(
echo [INFO] Aplikasi berhenti.
if not defined YHC_CHECK_ONLY pause
exit /b 1

:DONE
echo(
echo [INFO] Aplikasi berhenti.
if not defined YHC_CHECK_ONLY pause
exit /b 0
