#-*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
import sys

PY3 = sys.version_info[0] == 3

if PY3:
  install_requires = ["six"]
else:
  install_requires = ["six", "simplejson"]
README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()


setup(
    name='yandexwebdav',
    version='0.2.11',
    include_package_data=True,
    py_modules=['yandexwebdav'],
    url='https://github.com/lexich/yandex-disk-webdav',
    license='MIT',
    author='lexich',
    author_email='lexich121@gmail.com',
    description='Simple wrapper to work with yandex disk using webdav Basic Auth',
    long_description=README,
    install_requires=install_requires,
    scripts=[
        "ydw.py"
    ]
)
