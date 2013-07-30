#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

__author__ = 'lexich'
import os

import logging
import getpass
from optparse import OptionParser
import yandexwebdav

from six import u
from six import PY3
from six.moves import input

if PY3:
    import json
else:
    import simplejson as json

logger = logging.getLogger(__name__)


def _encode_utf8(txt):
    if not PY3:
        if type(txt) == unicode:
            return txt.encode("utf-8")
    return txt


class Config(object):
    def __init__(self, path=None):
        if not path:
            path = os.path.join(
                os.path.expanduser("~"),
                ".yandexwebdavconf"
            )
        if not os.path.exists(path):
            opt = self.createConfig(path)
        else:
            opt = self.readConfig(path)
        self._conf = yandexwebdav.Config(opt)

    @property
    def conf(self):
        return self._conf

    def readConfig(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def createConfig(self, path):
        opt = dict()

        opt["user"] = _encode_utf8(input(u("Input username: ")))
        opt["password"] = _encode_utf8(getpass.getpass(prompt="Input password: ", stream=sys.stderr))
        opt["host"] = u("webdav.yandex.ru")
        opt["limit"] = 4
        host = _encode_utf8(input(u("Input host defaultp[%s]: ") % opt["host"]))
        if host != "":
            opt["host"] = host
        try:
            opt["limit"] = int(input(u("Input thread limit default[%i]: ") % opt["limit"]))
        except ValueError:
            pass
        data = json.dumps(opt, indent=4, separators=(',', ': '))
        with open(path, "w") as f:
            f.write(data)
        return opt


def main():
    parser = OptionParser()
    parser.add_option("", "--list", dest="list",
                      action="store_true", default=False,
                      help="list of files and directories at remote server")
    parser.add_option("", "--sync", dest="sync",
                      action="store_true", default=False,
                      help="synchronize folder")
    parser.add_option("", "--mkdir", dest="mkdir",
                      action="store_true", default=False,
                      help="create remote folder", )
    parser.add_option("", "--download", dest="download",
                      action="store_true", default=False,
                      help="Download file to localstorage")
    parser.add_option("", "--delete", dest="delete",
                      action="store_true", default=False,
                      help="Delete file from remote server")

    parser.add_option("", "--upload", dest="upload",
                      action="store_true", default=False,
                      help="Upload file from localpath to remote server")
    parser.add_option("-l", "--local", dest="local", default="", help="local path")
    parser.add_option("-r", "--remote", dest="remote", default="", help="remote path")
    (opt, args) = parser.parse_args()

    conf = Config().conf

    def remote():
        if opt.remote == "":
            raise Exception("Need to input --remote (-r) param")
        return opt.remote

    def local():
        if opt.local == "":
            raise Exception("Need to input --local (-l) param")
        return opt.local

    if opt.list:
        logger.info("list %s" % remote())
        res = conf.list(remote())
        if res[0] is not None:
            for folder in res[0].keys():
                print("Folder: %s" % folder)
        if res[1] is not None:
            for filename in res[1].keys():
                print("File: %s" % filename)
    elif opt.sync:
        logger.info("sync %s" % remote())
        conf.sync(local(), remote())
    elif opt.mkdir:
        logger.info("mkdir %s" % remote())
        conf.mkdir(remote())
    elif opt.download:
        logger.info("download %s %s" % (local(), remote()))
        conf.downloadTo(remote(), local())
    elif opt.delete:
        logger.info("delete %s" % remote())
        conf.delete(remote())
    elif opt.upload:
        logger.info("upload %s %s" % (local(), remote()))
        conf.upload(local(), remote())


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(message)s",
        level=logging.DEBUG,
        datefmt='%m-%d-%y %H:%M'
    )
    try:
        main()
    except yandexwebdav.ConnectionException:
        e = sys.exc_info()[1]
        logger.exception(e)
