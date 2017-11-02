from distutils.core import setup, Extension
from Cython.Build import cythonize

names = ['acelib.bytes', 'acelib.packets', 'acelib.vxl', 'acelib.world', 'acelib.math3d']
modules = []
include = []

link_args = []
compile_args = []

for name in names:
    #                                                                 TODO: FIX THIS
    modules.append(Extension(name, [f"{name.replace('.', '/')}.pyx", "acelib/vxl_c.cpp"], language="c++", include_dirs=['acelib']))

setup(
    name='ext',
    ext_modules=cythonize(modules, annotate=True, compiler_directives={'language_level': 3})
)
