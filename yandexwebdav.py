#!/usr/bin/python
# coding=utf-8
import httplib
import base64
import xml.dom.minidom
import json
import os
import traceback

TRYINGS = 3


def _(path):
    if path is None:
        return u""
    try:
        return path.decode("UTF-8", errors='ignore')
    except UnicodeDecodeError, e:
        try:
            return path.encode("UTF-8", errors='ignore')
        except UnicodeEncodeError, e:
            return path


def log(txt):
    print(txt)


def err(txt):
    traceback.print_tb(txt)


class RemoteObject(object):
    def __init__(self, dom, config, root):
        self._dom = dom
        self._config = config
        self.root = root
        self.href = self._getEl("href")
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


class Config(object):
    def __init__(self, opts):
        """
        Constructor
        :param opts: dictionary of property
        :return: self
        """
        self.user = opts.get("user", "").encode("utf-8")
        self.password = opts.get("password", "").encode("utf-8")
        self.host = opts.get("host", "").encode("utf-8")
        self.options = opts

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
            log("list(%s): %s" % (iTry, href))
            try:
                href = os.path.join(u"/", _(href))
                conn = self.getConnection()
                conn.request("PROPFIND", href, "", self.getHeaders())
                response = conn.getresponse()
                data = response.read()
                if data == 'list: folder was not found':
                    return None, None
                else:
                    dom = xml.dom.minidom.parseString(data)
                    responces = dom.getElementsByTagNameNS("DAV:", "response")
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

    def sync(self, localpath, href, exclude=None):
        """
        Sync local and remote folders
        :param localpath: local folder
        :param href: remote folder
        :param exclude: filter folder which need to exlude
        :return: respose
        """
        log("sync: %s %s" % (localpath, href))
        try:
            localpath = _(localpath)
            href = _(href)
            localRoot, localFolders, localFiles = os.walk(localpath).next()
            remoteFolders, remoteFiles = self.list(href)
            if remoteFiles is None or remoteFolders is None:
                remoteFiles = {}
                remoteFolders = {}
                self.mkdir(href)

            foldersToCreate = filter(
                lambda folder: os.path.join(href, folder).decode("UTF-8") + u"/" not in remoteFolders,
                localFolders
            )

            for folder in foldersToCreate:
                folderPath = os.path.join(href, folder)
                self.mkdir(folderPath)

            filesToSync = filter(
                lambda lFile: os.path.join(href, lFile).decode("UTF-8") not in remoteFiles,
                localFiles
            )

            for f in filesToSync:
                localfilePath = os.path.join(localpath, f)
                remoteFilePath = os.path.join(href, f)
                self.upload(localfilePath, remoteFilePath)

            for folder in localFolders:
                localFolderPath = os.path.join(localpath, folder)
                remoteFolderPath = os.path.join(href, folder)
                if exclude:
                    bSync = exclude(localFolderPath, remoteFolderPath)
                else:
                    bSync = True
                if bSync:
                    self.sync(localFolderPath, remoteFolderPath, exclude)
        except Exception, e:
            err(e)

    def mkdir(self, href):
        """
        make remote folder
        :param href: remote path
        :return: response
        """
        for iTry in range(TRYINGS):
            log("mkdir(%s): %s" % (iTry, href))
            try:
                href = os.path.join(u"/", _(href))
                con = self.getConnection()
                con.request("MKCOL", href, "", self.getHeaders())
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
                log("download(%s): %s" % (iTry, href))
                href = os.path.join(u"/", _(href))
                conn = self.getConnection()
                conn.request("GET", href, "", self.getHeaders())
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
            log("downloadTo(%s): %s %s" % (iTry, href, localpath))
            try:
                href = os.path.join(u"/", _(href))
                localpath = _(localpath)

                conn = self.getConnection()
                conn.request("GET", href, "", self.getHeaders())
                responce = conn.getresponse()
                with open(localpath, "w") as f:
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
            log("delete(%s): %s" % (iTry, href))
            try:
                href = os.path.join(u"/", _(href))
                conn = self.getConnection()
                conn.request("DELETE", href, "", self.getHeaders())
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
        href = _(href)
        if os.path.islink(localpath):
            return self.upload(os.path.realpath(localpath), href)
            # 3 tryings to upload file
        for iTry in range(TRYINGS):
            log("upload(%s): %s %s" % (iTry, localpath, href))
            try:
                log
                "upload {0} {1}".format(localpath, href)
                href = os.path.join(u"/", href)
                conn = self.getConnection()
                headers = self.getHeaders()
                length = os.path.getsize(localpath)
                headers.update({
                    "Content-Type": "application/binary",
                    "Content-Length": length,
                    "Expect": "100-continue"
                })
                with open(localpath, "r") as f:
                    conn.request("PUT", href, f, headers)
                    response = conn.getresponse()
                    return response.read()
            except Exception, e:
                err(e)


class ConfigList(object):
    def __init__(self, path):
        self._configs = self.get_options(path)

    @property
    def config(self):
        return self._configs

    def get_options(self, path):
        with open(path, 'r') as f:
            options_list = json.load(f, "utf-8")
        return map(lambda opt: Config(opt), options_list)


if __name__ == "__main__":
    pass