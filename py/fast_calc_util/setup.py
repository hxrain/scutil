from distutils.core import setup
from Cython.Build import cythonize
setup(
    name='fast_calc_util',
    ext_modules=cythonize('fast_calc_util.pyx')
)

