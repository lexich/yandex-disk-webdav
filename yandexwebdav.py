#!/usr/bin/python
# coding=utf-8
import httplib
import base64
import xml.dom.minidom
import json
import os


class Responce(object):
    def __init__(self, dom, config, root):
        self._dom = dom
        self._config = config
        self.root = root
        self.href = self._getEl("href")
        self.length = self._getEl("getcontentlength")
        self.name = self._getEl("displayname")
        self.creationdate = self._getEl("creationdate")


    def _getEl(self, name):
        els = self._dom.getElementsByTagNameNS("DAV:", "href")
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
        self.user = opts.get("user", "").encode("utf-8")
        self.password = opts.get("password", "").encode("utf-8")
        self.host = opts.get("host", "").encode("utf-8")
        self.options = opts

    def getHeaders(self):
        return {
            "Depth": "1",
            "Authorization": 'Basic ' + base64.encodestring(self.user + ':' + self.password).strip(),
            "Accept": "*/*"
        }

    def getConnection(self):
        return httplib.HTTPSConnection(self.host)

    def list(self, href):
        folders = {}
        files = {}
        href = os.path.join("/", href)
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
                response = Responce(dom, self, href)
                if response.isFolder() and response.href != href:
                    folders[response.href] = response
                else:
                    files[response.href] = response
        return folders, files

    def sync(self, localpath, href, exclude=None):
        localRoot, localFolders, localFiles = os.walk(localpath).next()
        remoteFolders, remoteFiles = self.list(href)
        if remoteFiles == None or remoteFolders == None:
            remoteFiles = {}
            remoteFolders = {}
            self.mkdir(href)

        foldersToCreate = filter(
            lambda folder: unicode(os.path.join(href, folder)) + "/" not in remoteFolders,
            localFolders
        )

        for folder in foldersToCreate:
            folderPath = os.path.join(href, folder)
            self.mkdir(folderPath)

        filesToSync = filter(
            lambda lFile: unicode(os.path.join(href, lFile)) not in remoteFiles,
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

    def mkdir(self, href):
        href = os.path.join("/", href)
        con = self.getConnection()
        con.request("MKCOL", href, "", self.getHeaders())
        return con.getresponse().read()

    def download(self, href):
        href = os.path.join("/", href)
        conn = self.getConnection()
        conn.request("GET", href, "", self.getHeaders())
        return conn.getresponse().read()

    def downloadTo(self, href, localpath):
        href = os.path.join("/", href)

        conn = self.getConnection()
        conn.request("GET", href, "", self.getHeaders())
        responce = conn.getresponse()
        with open(localpath, "w") as f:
            while True:
                data = responce.read(1024)
                if not data:
                    break
                f.write(data)

    def delete(self, href):
        href = os.path.join("/", href)
        conn = self.getConnection()
        conn.request("DELETE", href, "", self.getHeaders())

    def upload(self, localpath, href):
        href = os.path.join("/", href)
        conn = self.getConnection()
        headers = self.getHeaders()
        length = os.path.getsize(localpath)
        headers.update({
            "Content-Type": "application/binary",
            "Content-Length": length,
            "Expect": "100-continue"
        })
        with open(localpath, "r") as f:
            data = f.read()
            conn.request("PUT", href, data, headers)
            response = conn.getresponse()
            return response.read()


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