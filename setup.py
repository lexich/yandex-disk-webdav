#-*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='yandex-disk-webdav',
    version='0.0.1',
    include_package_data=True,
    packages=find_packages(),
    url='https://github.com/lexich/yandex-disk-webdav',
    license='BSD',
    author='lexich',
    author_email='lexich121@gmail.com',
    description='Simple wrapper to work with yandex disk using webdav Basic Auth',
    long_description = open("README.md","r").read()
)