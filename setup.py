#-*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='yandexwebdav',
    version='0.2.2',
    include_package_data=True,
    py_modules=['yandexwebdav'],
    url='https://github.com/lexich/yandex-disk-webdav',
    license='BSD',
    author='lexich',
    author_email='lexich121@gmail.com',
    description='Simple wrapper to work with yandex disk using webdav Basic Auth',
    long_description="Simple wrapper to work with yandex disk using webdav Basic Auth",
    install_requires=[
        "simplejson","six"
    ],
    scripts=[
        "ydw.py"
    ]
)
