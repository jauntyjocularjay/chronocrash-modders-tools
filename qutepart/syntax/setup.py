#!/usr/bin/env python3
from setuptools import setup, Extension

include_dirs = ['/usr/include', '/usr/local/include', '/opt/local/include']
library_dirs = ['/usr/lib', '/usr/local/lib', '/opt/local/lib']

cParser = Extension(
    'cParser',
    sources=['cParser.c'],
    libraries=['pcre'],
    include_dirs=include_dirs,
    library_dirs=library_dirs,
)

setup(
    name='cParser',
    version='1.0',
    description='C Parser for Qutepart syntax highlighting',
    ext_modules=[cParser],
)
