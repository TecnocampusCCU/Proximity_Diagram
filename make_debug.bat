@echo off
set MYDIR=%cd%
for %%f in (%MYDIR%) do set directory=%%~nxf

rem Root OSGEO4W home dir to the same directory this script exists in
set QGIS_PATH="C:\Program Files\QGIS 3.16"
CALL %QGIS_PATH%\bin\o4w_env.bat
CALL %QGIS_PATH%\bin\qt5_env.bat
CALL %QGIS_PATH%\bin\py3_env.bat

@echo on
cmd /c "pyrcc5 -o resources.py resources.qrc"
cmd /c "rmdir /S /Q %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\%directory%"
cmd /c "xcopy ..\%directory% %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\%directory% /E /Q /I"
cmd /c "pause"
