#!/usr/bin/python
# coding=utf-8
import httplib
import base64
import xml.dom.minidom
import json
import os


class Responce(object):
    def __init__(self, dom, config):
        self._dom = dom
        self._config = config
        self.href = self._getEl("href")
        self.length = self._getEl("getcontentlength")
        self.name = self._getEl("displayname")
        self.creationdate = self._getEl("creationdate")

    def _getEl(self, name):
        els = self._dom.getElementsByTagNameNS("DAV:", "href")
        return els[0].firstChild.nodeValue if len(els) > 0 else ""

    def download(self):
        return self._config.download(self.href)

    def downloadTo(self, path):
        return self._config.downloadTo(self.href, path)

    def delete(self):
        return self._config.delete(self.href)

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
            "Authorization": 'Basic ' + base64.encodestring(self.user + ':' + self.password).strip()
        }

    def getConnection(self):
        return httplib.HTTPSConnection(self.host)

    def list(self, remotedir):
        conn = self.getConnection()
        conn.request("PROPFIND", remotedir, "", self.getHeaders())
        response = conn.getresponse()
        dom = xml.dom.minidom.parseString(response.read())
        responces = dom.getElementsByTagNameNS("DAV:", "response")
        return map(lambda dom: Responce(dom, self), responces)

    def download(self, href):
        conn = self.getConnection()
        conn.request("GET", href, "", self.getHeaders())
        return conn.getresponse().read()

    def downloadTo(self, href, path):
        conn = self.getConnection()
        conn.request("GET", href, "", self.getHeaders())
        responce = conn.getresponse()
        with open(path, "w") as f:
            while True:
                data = responce.read(1024)
                if not data:
                    break
                f.write(data)

    def delete(self, href):
        conn = self.getConnection()
        conn.request("DELETE", href, "", self.getHeaders())

    def upload(self, filename, remote):
        conn = self.getConnection()
        headers = self.getHeaders()
        length = os.path.getsize(filename)
        headers.update({
            "Content-Type": "application/binary",
            "Content-Length": length,
            "Expect": "100-continue"
        })
        with open(filename, "r") as f:
            data = f.read()
            conn.request("PUT", remote, data, headers)
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