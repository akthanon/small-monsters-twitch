@echo off
echo Instalando librerías Python...
echo.

REM Instalar las librerías usando pip
pip install -r requirements.txt

REM Comprobar si la instalación fue exitosa
if %errorlevel% neq 0 (
    echo Error: No se pudieron instalar todas las librerías correctamente.
    pause
    exit /b %errorlevel%
)

echo.
echo Instalación completada.
pause