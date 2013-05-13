yandex-disk-webdav
==================

Simple wrapper to work with yandex disk using webdav Basic Auth. 
Compatible python 2.6, 2.7, 3

# Install

> [pip](https://pypi.python.org/pypi/pip/) install [yandexwebdav](https://pypi.python.org/pypi/yandexwebdav)

Or

> [easy_install](https://pypi.python.org/pypi/setuptools) [yandexwebdav](https://pypi.python.org/pypi/yandexwebdav)

Or manual way

> python setup.py install

# Using API
> conf = Config({
> "name":"<-- username -->",
> "password":"<-- password -->"
> })

> conf.list(u"/") # list files and folder in root folder at remote server

> conf.sync(u"local folder", u"remote folder for upload files from local folder")

> conf.mkdir(u"path to remote folder, which you need to create")

> conf.download(u"path to remote file which your need to download") #function return file in bytearray

> conf.downloadTo(u"path to remote file which your need to download", u"local path to save file"):

> conf.delete(u"Delete remote file")

> conf.upload(u"path to local file", u"remote path for uploading file")

# Using interactive tool

> $ ydw.py -h

> Usage: ydw.py [options]

> Options:

>   -h, --help            show this help message and exit

>   --list                list of files and directories at remote server

>   --sync                synchronize folder

>   --mkdir               create remote folder

>   --download            Download file to localstorage

>   --delete              Delete file from remote server

>   --upload              Upload file from localpath to remote server

>   -l LOCAL, --local=LOCAL   local path

>   -r REMOTE, --remote=REMOTE  remote path

## Example

After first execution is appearead interactive configurator. You need to input your yandex name {username}@{ya.ru|yandex.ru}
password, host {webdaw.yandex.ru} and limit of threads, which used in parralel folder's sync.
Config saves in ~/.yandexwebdavconf

###List remote dir
> $ ydw.py --list -r //

> 05-12-13 00:43 - list /

> 05-12-13 00:43 - list(0): /

> Folder: /test/

> File: /test.png

> File: /test.mp4

###Sync local and remote folders
> $ ydw.py --sync -l /d/share/test -r //test

> 05-12-13 00:49 - sync /test

> 05-12-13 00:49 - sync: d:/share/test /test

> 05-12-13 00:49 - list(0): /test

> 05-12-13 00:49 - mkdir(0): /test

> 05-12-13 00:49 - upload(0): d:/share/test\test.txt /test/test.txt

###Create dir
> $ ydw.py --mkdir -r //test1

> 05-12-13 00:49 - mkdir /test1

> 05-12-13 00:49 - mkdir(0): /test1

###Download file
> $ ydw.py --download -l /d/share/test/test1.txt -r //test/test.txt

> 05-12-13 00:51 - download d:/share/test/test1.txt //test/test.txt

> 05-12-13 00:51 - downloadTo(0): //test/test.txt d:/share/test/test1.txt

###Delete file
> $ ydw.py --delete -r //test/test.txt

> 05-12-13 00:52 - delete //test/test.txt

> 05-12-13 00:52 - delete(0): //test/test.txt

###Upload file
> $ ydw.py --upload -l /d/share/test/test.txt -r //test/test.txt

> 05-12-13 00:53 - upload d:/share/test/test.txt //test/test.txt

> 05-12-13 00:53 - upload(0): d:/share/test/test.txt //test/test.txt
