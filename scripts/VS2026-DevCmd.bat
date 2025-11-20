@echo off
echo Setting up VS2026 Developer Command Prompt...
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64
echo.
echo Visual Studio 2026 environment ready!
echo MSVC Version: %VCToolsVersion%
echo VS Install Path: %VSINSTALLDIR%
echo.
