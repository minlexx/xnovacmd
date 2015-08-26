rem compiles application resources
rem modify Qt path to your own
rem python3 interpreter should already be in PATH

set QTDIR=V:\dev\Qt\5.5\msvc2010
set PATH=%QTDIR%\bin;%PATH%

cd ui
pyrcc5 res.qrc -o res_rc.py
pause