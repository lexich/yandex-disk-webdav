yandex-disk-webdav
==================

Simple wrapper to work with yandex disk using webdav Basic Auth

# Install
> pip install yandexwebdav
> easy_install yandexwebdav

# Using
> conf = Congif({
> "name":"<-- username -->",
> "password":"<-- password -->"
> })

> conf.list("/") # list files and folder in root folder at remote server
