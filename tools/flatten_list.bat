@echo off
setlocal EnableDelayedExpansion
rem Copies every file listed in flatten_list.txt (paths relative to source\archive) into .\flat
rem as source~archive~path~to~file so Claude can read deeply nested game files. Re-runnable.
set R=%~dp0
if not exist "%R%flat" mkdir "%R%flat"
set /a N=0
for /f "usebackq delims=" %%L in ("%R%flatten_list.txt") do (
  set "p=%%L"
  set "f=!p:\=~!"
  if exist "%R%source\archive\%%L" ( copy /y "%R%source\archive\%%L" "%R%flat\source~archive~!f!" >nul & set /a N+=1 ) else ( echo missing: %%L )
)
echo Done - !N! files copied to flat\
pause
