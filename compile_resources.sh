# Linux shell script
# compiles application resources
# Assumes Qt 5 is installed, as pyhton 3 and PyQt5

pyrcc5 ui/res.qrc -o ui/res_rc.py
