REM �˽ű���pyx��չcythonģ�����Ϊpyd
python setup.py build

copy build\lib.win-amd64-3.7\fast_calc_util.cp37-win_amd64.pyd ..\
del fast_calc_util.c
rmdir /S /Q build
pause