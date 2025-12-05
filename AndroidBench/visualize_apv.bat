@echo off
REM WTG Visualization Script for APV
REM This script compiles the visualization client and runs the analysis

echo ========================================================================
echo WTG Visualization Tool for APV
echo ========================================================================
echo.

echo [1/4] Compiling WTG Visualization Client...
cd /d "%~dp0..\SootAndroid"
call ant compile
if errorlevel 1 (
    echo Error: Compilation failed
    pause
    exit /b 1
)

echo.
echo [2/4] Running Gator analysis with visualization...
cd /d "%~dp0"
python runGator.py -j apv/config.json -p apv

echo.
echo [3/4] Looking for generated files...
set HTML_FILE=
set OUTPUT_DIR=%~dp0..\output\apv\results
if exist "%OUTPUT_DIR%" (
    for %%f in ("%OUTPUT_DIR%\*_wtg_viewer.html") do set HTML_FILE=%%f
)

if not defined HTML_FILE (
    echo Warning: HTML viewer not found
    goto :end
)

echo Found: %HTML_FILE%
echo.
echo [4/4] Opening visualization in browser...
start "" "%HTML_FILE%"

echo.
echo ========================================================================
echo SUCCESS!
echo ========================================================================
echo The WTG visualization should now be open in your browser.
echo.
echo Files location: output\apv\
echo   - Results: output\apv\results\
echo   - Source:  output\apv\source\ (if --keep-decoded-apk-dir used)
echo.
echo To visualize the graph:
echo   1. Use the HTML viewer (already opened)
echo   2. Copy DOT content from the 'DOT File' tab
echo   3. Paste at: https://dreampuf.github.io/GraphvizOnline/
echo.

:end
pause
