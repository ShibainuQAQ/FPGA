@echo off
chcp 65001 >nul
REM ============================================================
REM  DPWM one-click regression simulation (batch mode, no Vivado GUI)
REM  Usage: double-click this file inside 03-FPGA工程\sim\
REM  Compiles ..\rtl\dpwm_core.v + tb_dpwm.v, runs the 5 checks.
REM  If Vivado lives elsewhere, edit VIVADO_BIN below.
REM  (This file is kept ASCII-only on purpose: Chinese text in a
REM   .bat gets garbled by cmd's code page. See README.md instead.)
REM ============================================================
set VIVADO_BIN=D:\Xilinx\Vivado\2022.2\bin
set PATH=%VIVADO_BIN%;%PATH%
cd /d "%~dp0"

echo [1/3] xvlog - compile ...
call xvlog.bat ..\rtl\dpwm_core.v tb_dpwm.v
if errorlevel 1 goto err

echo [2/3] xelab - elaborate ...
call xelab.bat -debug typical tb_dpwm -s tb_dpwm_sim
if errorlevel 1 goto err

echo [3/3] xsim - run ...
call xsim.bat tb_dpwm_sim -runall
if errorlevel 1 goto err
goto end

:err
echo.
echo *** ERROR: read the last lines above ***
pause
exit /b 1

:end
echo.
echo Simulation finished. Double-click again to re-run.
pause
