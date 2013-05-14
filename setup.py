#-*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
setup(
    name='yandexwebdav',
    version='0.2.4',
    include_package_data=True,
    py_modules=['yandexwebdav'],
    url='https://github.com/lexich/yandex-disk-webdav',
    license='BSD',
    author='lexich',
    author_email='lexich121@gmail.com',
    description='Simple wrapper to work with yandex disk using webdav Basic Auth',
    long_description=README,
    install_requires=[
        "simplejson","six"
    ],
    scripts=[
        "ydw.py"
    ]
)
