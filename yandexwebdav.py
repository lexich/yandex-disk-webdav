#!/usr/bin/python
# coding=utf-8
import httplib
import base64
import xml.dom.minidom
import os
import traceback
import urllib
import threading
from Queue import Queue, Empty

TRYINGS = 3


def _(path):
    if path is None:
        return u""
    elif type(path) == unicode:
        return path
    try:
        return path.decode(u"UTF-8", errors=u'ignore')
    except UnicodeDecodeError, e:
        return path


def log(txt):
    print(txt)


def err(*args):
    print args
    traceback.print_exc()


def remote(href):
    href = _(href)
    href = os.path.join(u"/", href)
    return href


class RemoteObject(object):
    def __init__(self, dom, config, root):
        self._dom = dom
        self._config = config
        self.root = root
        href = self._getEl(u"href")
        if type(href) == unicode:
            href = href.encode("utf-8")
        self.href = urllib.unquote(href).decode("utf-8")
        self.length = self._getEl(u"getcontentlength")
        self.name = self._getEl(u"displayname")
        self.creationdate = self._getEl(u"creationdate")

    def _getEl(self, name):
        els = self._dom.getElementsByTagNameNS(u"DAV:", name)
        return els[0].firstChild.nodeValue if len(els) > 0 else ""

    def isFolder(self):
        els = self._dom.getElementsByTagNameNS(u"DAV:", u"collection")
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


qWork = Queue()


def __call():
    while True:
        try:
            name, func, args = qWork.get()
            func(*args)
            qWork.task_done()
        except Empty, e:
            pass
        except Exception, e:
            err("Exception: {0}".format(name))


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


class Config(object):
    def __init__(self, opts):
        """
        Constructor
        :param opts: dictionary of property
        :return: self
        """
        self.user = opts.get(u"user", u"").encode(u"utf-8")
        self.password = opts.get(u"password", u"").encode(u"utf-8")
        self.host = opts.get(u"host", u"webdav.yandex.ru").encode(u"utf-8")
        self.options = opts
        self.limit = opts.get(u"limit", 4)

    def getHeaders(self):
        """
        Get common headers
        :return:
        """
        return {
            "Depth": "1",
            "Authorization": 'Basic ' + base64.encodestring(self.user + ':' + self.password).strip(),
            "Accept": "*/*"
        }

    def getConnection(self):
        """
        Get connection
        :return: connection httplib.HTTPSConnection
        """
        return httplib.HTTPSConnection(self.host)

    def list(self, href):
        """
        list of files and directories at remote server
        :param href: remote folder
        :return: list(folders, files) and list(None,None) if folder doesn't exist
        """
        for iTry in range(TRYINGS):
            log(u"list(%s): %s" % (iTry, href))
            try:
                href = os.path.join(u"/", _(href))
                conn = self.getConnection()
                conn.request("PROPFIND", href.encode("utf-8", errors=u'ignore'), u"", self.getHeaders())
                response = conn.getresponse()
                data = response.read()
                if data == 'list: folder was not found':
                    return None, None
                else:
                    dom = xml.dom.minidom.parseString(data)
                    responces = dom.getElementsByTagNameNS(u"DAV:", u"response")
                    folders = {}
                    files = {}
                    for dom in responces:
                        response = RemoteObject(dom, self, href)
                        if response.isFolder() and response.href != href:
                            folders[response.href] = response
                        else:
                            files[response.href] = response
                return folders, files
            except Exception, e:
                err(e)

    def sync(self, localpath, href, exclude=None, block=True):
        """
        Sync local and remote folders
        :param localpath: local folder
        :param href: remote folder
        :param exclude: filter folder which need to exlude
        :return: respose
        """
        log(u"sync: %s %s" % (localpath, href))
        try:
            localpath = _(localpath)
            href = remote(href)
            localRoot, localFolders, localFiles = os.walk(localpath).next()
            remoteFolders, remoteFiles = self.list(href)
            if remoteFiles is None or remoteFolders is None:
                remoteFiles = {}
                remoteFolders = {}
                self.mkdir(href)

            foldersToCreate = filter(
                lambda folderPath: folderPath not in remoteFolders,
                map(lambda folder: os.path.join(href, _(folder)) + u"/",
                    localFolders)
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
                        [(localFolderPath, remoteFolderPath),]
                    )
        except Exception, e:
            err(e)
        if block:
            qWork.join()

    def mkdir(self, href):
        """
        make remote folder
        :param href: remote path
        :return: response
        """
        for iTry in range(TRYINGS):
            log(u"mkdir(%s): %s" % (iTry, href))
            try:
                href = remote(href)
                con = self.getConnection()
                con.request("MKCOL", href.encode("utf-8", errors=u'ignore'), "", self.getHeaders())
                return con.getresponse().read()
            except Exception, e:
                err(e)

    def download(self, href):
        """
        Download file and return response
        :param href: remote path
        :return: file responce
        """
        for iTry in range(TRYINGS):
            try:
                log(u"download(%s): %s" % (iTry, href))
                href = remote(href)
                conn = self.getConnection()
                conn.request("GET", href.encode("utf-8", errors=u'ignore'), "", self.getHeaders())
                return conn.getresponse().read()
            except Exception, e:
                err(e)

    def downloadTo(self, href, localpath):
        """
        Download file to localstorage
        :param href: remote path
        :param localpath: local path
        :return: response
        """
        for iTry in range(TRYINGS):
            log(u"downloadTo(%s): %s %s" % (iTry, href, localpath))
            try:
                href = remote(href)
                localpath = _(localpath)

                conn = self.getConnection()
                conn.request("GET", href.encode("utf-8", errors=u'ignore'), "", self.getHeaders())
                responce = conn.getresponse()
                with open(localpath, u"w") as f:
                    while True:
                        data = responce.read(1024)
                        if not data:
                            break
                        f.write(data)
                return True
            except Exception, e:
                err(e)

    def delete(self, href):
        """
        Delete file from remote server
        :param href: remote path
        :return: response
        """
        for iTry in range(TRYINGS):
            log(u"delete(%s): %s" % (iTry, href))
            try:
                href = remote(href)
                conn = self.getConnection()
                conn.request("DELETE", href.encode("utf-8", errors=u'ignore'), "", self.getHeaders())
                return conn.getresponse().read()
            except Exception, e:
                err(e)

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
            log(u"ERROR: localfile: %s not found" % localpath)
            return
        if os.path.islink(localpath):
            return self.upload(os.path.abspath(os.path.realpath(localpath)), href)
            # 3 tryings to upload file
        for iTry in range(TRYINGS):
            log(u"upload(%s): %s %s" % (iTry, localpath, href))
            try:
                href = os.path.join(u"/", href)
                conn = self.getConnection()
                headers = self.getHeaders()
                length = os.path.getsize(localpath)
                headers.update({
                    "Content-Type": "application/binary",
                    "Content-Length": length,
                    "Expect": "100-continue"
                })
                with open(localpath.encode("utf-8", errors=u'ignore'), u"r") as f:
                    href = href.encode("utf-8", errors=u'ignore')
                    href = urllib.quote(href)
                    conn.request("PUT", href, f, headers)
                    response = conn.getresponse()
                    return response.read()
            except Exception, e:
                err(e)


if __name__ == "__main__":
    pass
