#!/usr/bin/python
# coding=utf-8

import os
import sys
import threading
import logging
import base64
import xml.dom.minidom

from six.moves import queue
from six.moves import http_client
from six import u, b, PY3

if PY3:
    from urllib.parse import unquote, quote
else:
    from urllib import unquote, quote

logger = logging.getLogger("yandexwebdav.py")

TRYINGS = 3


def _encode_utf8(txt):
    if not PY3:
        if type(txt) == unicode:
            return txt.encode("utf-8")
    return txt


def _decode_utf8(txt):
    if PY3:
        if type(txt) is str:
            return txt
    return txt.decode("utf-8")


def _(path):
    """
    Normalize path to unicode
    :param path: path
    :return: normalize path

    >>> _(None)
    u''
    >>> _(u("test1"))
    u'test1'
    >>> _("test2")
    u'test2'
    """
    if path is None:
        return u("")
    if not PY3:
        if type(path) == unicode:
            return path
        try:
            return _decode_utf8(path)
        except UnicodeDecodeError:
            pass
    return path


def remote(href):
    """
    Normalize remote href
    :param href: remote path
    :return: normalize href

    >>> remote("/test/hello.txt")
    u'/test/hello.txt'
    >>> remote("test/hello.txt")
    u'/test/hello.txt'
    >>> remote("test\hello.txt")
    u'/test/hello.txt'
    >>> remote(None)
    u'/'
    """
    href = _(href)
    href = os.path.join(u("/"), href)
    if os.sep == "\\":
        href = href.replace("\\", "/")
    return href


class RemoteObject(object):
    def __init__(self, dom, config, root):
        self._dom = dom
        self._config = config
        self.root = root
        href = self._getEl("href")

        href = _encode_utf8(href)
        self.href = _decode_utf8(unquote(href))
        self.length = self._getEl("getcontentlength")
        self.name = self._getEl("displayname")
        self.creationdate = self._getEl("creationdate")

    def _getEl(self, name):
        els = self._dom.getElementsByTagNameNS("DAV:", name)
        return els[0].firstChild.nodeValue if len(els) > 0 else ""

    def isFolder(self):
        els = self._dom.getElementsByTagNameNS("DAV:", "collection")
        return len(els) > 0

    def download(self):
        return self._config.download(self.href)

    def downloadTo(self, path):
        return self._config.downloadTo(self.href, path)

    def delete(self):
        return self._config.delete(self.href)

    def list(self):
        if self.isFolder() and self.href != self.root:
            return self._config.list(os.path.join(self.root, self.href))
        return []

    def __str__(self):
        return self.href

    def __unicode__(self):
        return self.href


qWork = queue.Queue()


def __call():
    while True:
        try:
            name, func, args = qWork.get()
            func(*args)
            qWork.task_done()
        except queue.Empty:
            pass
        except Exception:
            e = sys.exc_info()[1]
            print("Exception: {0} {1}".format(name, e))


threadsContainer = []


def apply_async(name, func, params_list, limit=5):
    for params in params_list:
        if type(params) is list or type(params) is tuple:
            item = (name, func, params)
        else:
            item = (name, func, [params, ])
        res = qWork.put_nowait(item)

    if len(threadsContainer) > 0:
        return
    for i in range(limit):
        t = threading.Thread(target=__call)
        t.daemon = True
        threadsContainer.append(t)
    for th in threadsContainer:
        th.start()


class ConnectionException(Exception):
    """docstring for NotAuthException"""

    def __init__(self, code, msg=""):
        strError = _("Not Authorization status code: {0}\n{1}").format(code, msg)
        self.code = code
        super(ConnectionException, self).__init__(strError)


def checkResponse(response, msg=""):
    if response.status not in [200, 201, 207]:
        raise ConnectionException(response.status, msg)


class Config(object):
    def __init__(self, opts):
        """
        Constructor
        :param opts: dictionary of property
        :return: self
        """
        self.user = _encode_utf8(opts.get("user", ""))
        self.password = _encode_utf8(opts.get("password", ""))
        self.host = _encode_utf8(opts.get("host", "webdav.yandex.ru"))
        self.options = opts
        self.limit = opts.get("limit", 4)

    def getHeaders(self):
        """
        Get common headers
        :return:
        """
        basicauth = base64.encodestring(b(self.user + ':' + self.password)).strip()
        return {
            "Depth": "1",
            "Authorization": 'Basic ' + _decode_utf8(basicauth),
            "Accept": "*/*"
        }

    def getConnection(self):
        """
        Get connection
        :return: connection http_client.HTTPSConnection
        """
        return http_client.HTTPSConnection(self.host)

    def list(self, href):
        """
        list of files and directories at remote server
        :param href: remote folder
        :return: list(folders, files) and list(None,None) if folder doesn't exist
        """
        for iTry in range(TRYINGS):
            logger.info(u("list(%s): %s") % (iTry, href))
            folders = None
            files = None
            try:
                href = os.path.join(u("/"), _(href))
                conn = self.getConnection()
                conn.request("PROPFIND", _encode_utf8(href), u(""), self.getHeaders())
                response = conn.getresponse()
                checkResponse(response)
                data = response.read()
                if data == b('list: folder was not found'):
                    return folders, files
                elif data == b('You are not authorized to see this!'):
                    return folders, files
                else:
                    try:
                        dom = xml.dom.minidom.parseString(data)
                        responces = dom.getElementsByTagNameNS("DAV:", "response")
                        folders = {}
                        files = {}
                        for dom in responces:
                            response = RemoteObject(dom, self, href)
                            if response.href != href:
                                if response.isFolder():
                                    folders[response.href] = response
                                else:
                                    files[response.href] = response
                    except xml.parsers.expat.ExpatError:
                        e = sys.exc_info()[1]
                        logger.exception(e)
                return folders, files
            except ConnectionException:
                raise
            except Exception:
                e = sys.exc_info()[1]
                logger.exception(e)
            return folders, files

    def sync(self, localpath, href, exclude=None, block=True):
        """
        Sync local and remote folders
        :param localpath: local folder
        :param href: remote folder
        :param exclude: filter folder which need to exlude
        :return: respose
        """
        logger.info(u("sync: %s %s") % (localpath, href))
        try:
            localpath = _(localpath)
            href = remote(href)
            localRoot, localFolders, localFiles = next(os.walk(localpath))
            remoteFolders, remoteFiles = self.list(href)
            if remoteFiles is None or remoteFolders is None:
                remoteFiles = {}
                remoteFolders = {}
                self.mkdir(href)

            def norm(folder):
                path = os.path.join(href, _(folder))
                if path[len(path) - 1] != os.path.sep:
                    path += u("/")
                return path

            foldersToCreate = filter(
                lambda folderPath: folderPath not in remoteFolders,
                map(norm, localFolders)
            )
            apply_async("mkdir", lambda path: self.mkdir(path), foldersToCreate, self.limit)

            filesToSync = filter(
                lambda lFile: os.path.join(href, _(lFile)) not in remoteFiles,
                localFiles
            )
            fileArgs = [(os.path.join(localpath, f), os.path.join(href, f))
                        for f in filesToSync]
            apply_async("upload", lambda s, t: self.upload(s, t), fileArgs, self.limit)

            for folder in localFolders:
                localFolderPath = os.path.join(localpath, folder)
                remoteFolderPath = os.path.join(href, folder)
                if exclude:
                    bSync = exclude(localFolderPath, remoteFolderPath)
                else:
                    bSync = True
                if bSync:
                    apply_async(
                        "sync",
                        lambda localpath, href: self.sync(localpath, href, exclude, False),
                        [(localFolderPath, remoteFolderPath), ]
                    )
        except ConnectionException:
            raise
        except Exception:
            e = sys.exc_info()[1]
            logger.exception(e)
        if block:
            qWork.join()

    def mkdir(self, href):
        """
        create remote folder
        :param href: remote path
        :return: response
        """
        for iTry in range(TRYINGS):
            logger.info(u("mkdir(%s): %s") % (iTry, href))
            try:
                href = remote(href)
                con = self.getConnection()
                con.request("MKCOL", _encode_utf8(href), "", self.getHeaders())
                response = con.getresponse()
                checkResponse(response)
                return response.read()
            except ConnectionException:
                raise
            except Exception:
                e = sys.exc_info()[1]
                logger.exception(e)

    def download(self, href):
        """
        Download file and return response
        :param href: remote path
        :return: file responce
        """
        for iTry in range(TRYINGS):
            try:
                logger.info(u("download(%s): %s") % (iTry, href))
                href = remote(href)
                conn = self.getConnection()
                conn.request("GET", _encode_utf8(href), "", self.getHeaders())
                response = conn.getresponse()
                checkResponse(response, "href={0}".format(href))
                data = response.read()
                if data == b('resource not found'):
                    return b("")
                else:
                    return data
            except ConnectionException:
                raise
            except Exception:
                e = sys.exc_info()[1]
                logger.exception(e)

    def downloadTo(self, href, localpath):
        """
        Download file to localstorage
        :param href: remote path
        :param localpath: local path
        :return: response
        """
        for iTry in range(TRYINGS):
            logger.info(u("downloadTo(%s): %s %s") % (iTry, href, localpath))
            try:
                href = remote(href)
                localpath = _(localpath)

                conn = self.getConnection()
                conn.request("GET", _encode_utf8(href), "", self.getHeaders())
                response = conn.getresponse()
                checkResponse(response)
                f = None
                try:
                    while True:
                        data = _decode_utf8(response.read(1024))
                        if not data:
                            break
                        if data == u('resource not found'):
                            return False
                        if not f:
                            f = open(localpath, "w")
                        f.write(data)
                finally:
                    if f:
                        f.close()
                return True
            except ConnectionException:
                raise
            except Exception:
                e = sys.exc_info()[1]
                logger.exception(e)

    def delete(self, href):
        """
        Delete file from remote server
        :param href: remote path
        :return: response
        """
        for iTry in range(TRYINGS):
            logger.info(u("delete(%s): %s") % (iTry, href))
            try:
                href = remote(href)
                conn = self.getConnection()
                conn.request("DELETE", _encode_utf8(href), "", self.getHeaders())
                response = conn.getresponse()
                checkResponse(response)
                return response.read()
            except ConnectionException:
                raise
            except Exception:
                e = sys.exc_info()[1]
                logger.exception(e)

    def write(self, f, href, length=None):
        logger.info(u("write: %s") % href)
        href = remote(href)
        href = os.path.join(u("/"), href)
        try:
            conn = self.getConnection()
            headers = self.getHeaders()
            headers.update({
                "Content-Type": "application/binary",
                "Expect": "100-continue"
            })
            if length:
                headers["Content-Length"] = length
            href = _encode_utf8(href)
            href = quote(href)
            conn.request("PUT", href, f, headers)
            response = conn.getresponse()
            checkResponse(response)
            data = response.read()
            return data
        except ConnectionException:
            raise
        except Exception:
            e = sys.exc_info()[1]
            logger.exception(e)

    def upload(self, localpath, href):
        """
        Upload file from localpath to remote server
        :param localpath: local path
        :param href: remote path
        :return: response
        """
        localpath = _(localpath)
        href = remote(href)
        if not os.path.exists(localpath):
            logger.info(u("ERROR: localfile: %s not found") % localpath)
            return
        if os.path.islink(localpath):
            return self.upload(os.path.abspath(os.path.realpath(localpath)), href)
            # 3 tryings to upload file
        for iTry in range(TRYINGS):
            try:
                logger.info(u("upload: %s %s") % (localpath, href))
                length = os.path.getsize(localpath)

                if PY3:
                    _open = open(_encode_utf8(localpath), "r", encoding='latin-1')
                else:
                    _open = open(_encode_utf8(localpath), "r")
                with _open as f:
                    return self.write(f, href, length=length)
            except ConnectionException:
                raise
            except Exception:
                e = sys.exc_info()[1]
                logger.exception(e)


if __name__ == "__main__":
    pass
