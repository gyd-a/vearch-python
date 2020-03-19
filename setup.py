from setuptools import setup
from setuptools.extension import Extension
from distutils.command.build import build
from distutils.command.build_ext import build_ext
from distutils.util import get_platform
import os

long_description="""
Vearch is the vector search infrastructure for deeping learning and AI applications. 
The Python's implementation allows vearch to be used locally.
"""

class CustomBuild(build):
    """Build ext first so that swig-generated file is packaged.
    """
    sub_commands = [
        ('build_ext', build.has_ext_modules),
        ('build_py', build.has_pure_modules),
        ('build_clib', build.has_c_libraries),
        ('build_scripts', build.has_scripts),
    ]


class CustomBuildExt(build_ext):
    """Customize extension build.
    """

    def run(self):
        # Import NumPy only at runtime.
        import numpy
        self.include_dirs.append(numpy.get_include())
        link_flags = os.getenv('GAMMA_LDFLAGS')
        if link_flags:
            if self.link_objects is None:
                self.link_objects = []
            for flag in link_flags.split():
                self.link_objects.append(flag.strip())
        else:
            self.libraries.append('gamma')
        build_ext.run(self)

    def build_extensions(self):
        # Suppress -Wstrict-prototypes bug in python.
        # https://stackoverflow.com/questions/8106258/
        self._remove_flag('-Wstrict-prototypes')
        # Remove clang-specific flag.
        compiler_name = self.compiler.compiler[0]
        if 'gcc' in compiler_name or 'g++' in compiler_name:
            self._remove_flag('-Wshorten-64-to-32')
        build_ext.build_extensions(self)

    def _remove_flag(self, flag):
        compiler = self.compiler.compiler
        compiler_cxx = self.compiler.compiler_cxx
        compiler_so = self.compiler.compiler_so
        for args in (compiler, compiler_cxx, compiler_so):
            while flag in args:
                args.remove(flag)


_swigvearch = Extension(
    'vearch._swigvearch',
    sources=['python/swigvearch.i'],
    define_macros=[('FINTEGER', 'int')],
    language='c++',
    include_dirs=[
        os.getenv('GAMMA_INCLUDE', '/usr/local/include'),
    ],
    extra_compile_args=[
        '-std=c++11', '-mavx2', '-mf16c', '-msse4', '-mpopcnt', '-m64',
        '-Wno-sign-compare', '-fopenmp'
    ],
    extra_link_args=['-fopenmp'],
    swig_opts=[
        '-c++', '-Doverride=', 
        '-I' + os.getenv('GAMMA_INCLUDE', '/usr/local/include'),
    ] + ([] if 'macos' in get_platform() else ['-DSWIGWORDSIZE64'])
)

setup(
    name='vearch',
    version='0.3.0.6',
    description='A library for efficient similarity search and storage of deep learning vectors.',
    long_description=long_description,
    url='https://github.com/vearch/vearch',
    author='Haifeng Liu, Jie Li, Xingda Wang, Dabin Xie, Chao Zhan',
    author_email='vearch-maintainers@groups.io',
    license='Apache License, Version 2.0',
    keywords='real time index, vector nearest neighbors',
 
    cmdclass={
        'build': CustomBuild,
        'build_ext': CustomBuildExt,
    },
    install_requires=['numpy>=1.16.0', 'parasail'],
    package_dir={'vearch': 'python'},
    packages=['vearch'],
    ext_modules=[_swigvearch]
)