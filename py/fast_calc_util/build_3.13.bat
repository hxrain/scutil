REM 此脚本将pyx扩展cython模块编译为pyd
D:\Python\python313\python setup.py build

copy build\lib.win-amd64-cpython-313\fast_calc_util.cp313-win_amd64.pyd ..\
del fast_calc_util.c
rmdir /S /Q build
pause