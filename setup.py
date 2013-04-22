#-*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='yandexwebdav',
    version='0.0.3',
    include_package_data=True,
    packages=find_packages(),
    url='https://github.com/lexich/yandex-disk-webdav',
    license='BSD',
    author='lexich',
    author_email='lexich121@gmail.com',
    description='Simple wrapper to work with yandex disk using webdav Basic Auth',
    long_description = "Simple wrapper to work with yandex disk using webdav Basic Auth"
)
