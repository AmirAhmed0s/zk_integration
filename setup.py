# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

# get version from __version__ variable in zk_integration/__init__.py
from zk_integration import __version__ as version

setup(
    name='zk_integration',
    version=version,
    description='ZK Device Integration',
    author='Peter',
    author_email='eng.peter.maged@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
)
