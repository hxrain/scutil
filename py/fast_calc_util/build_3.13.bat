REM �˽ű���pyx��չcythonģ�����Ϊpyd
D:\Python\python313\python setup.py build

copy build\lib.win-amd64-cpython-313\fast_calc_util.cp313-win_amd64.pyd ..\
del fast_calc_util.c
rmdir /S /Q build
pause