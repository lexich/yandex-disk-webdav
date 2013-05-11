# -*- coding: utf-8 -*-
import sys

__author__ = 'lexich'
import os
import logging
import getpass
from optparse import OptionParser
import yandexwebdav
import simplejson

logger = logging.getLogger(__name__)


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
            return simplejson.load(f)

    def createConfig(self, path):
        opt = dict()

        opt["user"] = raw_input(u"Input username: ").encode("utf-8")
        opt["password"] = getpass.getpass(prompt="Input password: ", stream=sys.stderr).encode("utf-8")
        opt["host"] = u"webdav.yandex.ru"
        opt["limit"] = 4
        host = raw_input(u"Input host defaultp[%s]: " % opt["host"]).encode("utf-8")
        if host != "":
            opt["host"] = host
        try:
            opt["limit"] = int(raw_input(u"Input thread limit default[%i]: " % opt["limit"]))
        except ValueError:
            pass
        data = simplejson.dumps(opt, indent=4, separators=(',', ': '))
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
        logger.info(u"list %s" % remote())
        res = conf.list(remote())
        for folder in res[0].keys():
            print(u"Folder: %s" % folder)
        for filename in res[1].keys():
            print(u"File: %s" % filename)
    elif opt.sync:
        logger.info(u"sync %s" % remote())
        conf.sync(local(), remote())
    elif opt.mkdir:
        logger.info(u"mkdir %s" % remote())
        conf.mkdir(remote())
    elif opt.download:
        logger.info(u"download %s %s" % (local(), remote()))
        conf.downloadTo(remote(), local())
    elif opt.delete:
        logger.info(u"delete %s" % remote())
        conf.delete(remote())
    elif opt.upload:
        logger.info(u"upload %s %s" % (local(), remote()))
        conf.upload(local(), remote())


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(message)s",
        level=logging.DEBUG,
        datefmt='%m-%d-%y %H:%M'
    )
    main()