__author__ = 'lexich'

import unittest
import ydw
import yandexwebdav
from six import b
from six.moves import http_client
from random import random
import tempfile
import os


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.conf = ydw.Config().conf

    def test_init(self):
        self.assertTrue(self.conf.user != "")
        self.assertTrue(self.conf.password != "")
        self.assertTrue(self.conf.host != "")
        self.assertTrue(self.conf.limit != "")

    def test_getHeaders(self):
        headers = self.conf.getHeaders()
        self.assertTrue("Depth" in headers.keys())
        self.assertTrue("Accept" in headers.keys())
        self.assertTrue("Authorization" in headers.keys())
        self.assertTrue("Basic " in headers.get("Authorization"))

    def test_getConnection(self):
        connection = self.conf.getConnection()
        self.assertTrue(isinstance(connection, http_client.HTTPSConnection))

    def test_list(self):
        folders, files = self.conf.list("/")
        self.assertFalse(folders is None)
        self.assertFalse(files is None)
        self.assertEqual(type(folders), dict)
        self.assertEqual(type(files), dict)
        self.assertFalse("/" in folders.keys())
        self.assertFalse("/" in files.keys())

    def test_mkdir_and_deletefolder(self):
        name = "/test_%0.4f/" % random()
        folders, files = self.conf.list("/")
        self.assertFalse(name in folders.keys())
        response = self.conf.mkdir(name)
        self.assertEqual(response, b(""))
        folders, files = self.conf.list("/")
        self.assertTrue(name in folders.keys())
        self.conf.delete(name)
        folders, files = self.conf.list("/")
        self.assertFalse(name in folders.keys())

    def test_fakedownloadTo(self):
        filename = "fakedowload%0.4f.txt" % random()
        filenamePath = "/%s" % filename

        localfile = os.path.join(tempfile.gettempdir(), filename)
        folders, files = self.conf.list("/")
        self.assertFalse(filenamePath in files.keys())
        self.assertRaises(yandexwebdav.ConnectionException, self.conf.download, filenamePath)
        self.assertRaises(yandexwebdav.ConnectionException, self.conf.downloadTo, filenamePath, localfile)
        self.assertFalse(os.path.exists(localfile))


TMPNAME = "_test_%s" % random()


class TestSyncUpload(unittest.TestCase):
    def setUp(self):
        self.conf = ydw.Config().conf
        self.tmppath = os.path.join(
            tempfile.gettempdir(),
            TMPNAME
        )
        self.remotedir = "/test_%0.4f/" % random()
        self.file1 = os.path.join(self.tmppath, "file1.txt")
        self.file2 = os.path.join(self.tmppath, "file2.txt")
        self.folder1 = os.path.join(self.tmppath, "folder1")
        os.mkdir(self.tmppath)
        os.mkdir(self.folder1)
        with open(self.file1, "w") as f:
            f.write("file1")
        with open(self.file2, "w") as f:
            f.write("file2")

    def tearDown(self):
        os.remove(self.file1)
        os.remove(self.file2)
        if os.path.exists(self.folder1):
            os.rmdir(self.folder1)
        if os.path.exists(self.tmppath):
            os.rmdir(self.tmppath)

    def test_upload_download_downloadTo_deletefile(self):
        filename = "/test_%0.4f.txt" % random()
        folders, files = self.conf.list("/")
        self.assertFalse(filename in files.keys())

        self.conf.upload(self.file1, filename)
        folders, files = self.conf.list("/")
        self.assertTrue(filename in files.keys())

        data = self.conf.download(filename)
        self.assertEqual(data, b("file1"))

        downloadTo = os.path.join(self.tmppath, "download.txt")
        self.conf.downloadTo(filename, downloadTo)

        self.assertTrue(os.path.exists(downloadTo))

        with open(downloadTo, "r") as f:
            data = f.read()
        self.assertEqual(data, "file1")
        os.remove(downloadTo)

        self.conf.delete(filename)

        folders, files = self.conf.list("/")
        self.assertFalse(filename in files.keys())

    def test_write_download_delete(self):
        filename = "/test_%0.4f.txt" % random()
        folders, files = self.conf.list("/")
        self.assertFalse(filename in files.keys())

        with open(self.file1, "r") as f:
            self.conf.write(f, filename)

        folders, files = self.conf.list("/")
        self.assertTrue(filename in files.keys())

        data = self.conf.download(filename)
        self.assertEqual(data, b("file1"))

        downloadTo = os.path.join(self.tmppath, "download.txt")
        self.conf.downloadTo(filename, downloadTo)

        self.assertTrue(os.path.exists(downloadTo))

        with open(downloadTo, "r") as f:
            data = f.read()
        self.assertEqual(data, "file1")
        os.remove(downloadTo)

        self.conf.delete(filename)

        folders, files = self.conf.list("/")
        self.assertFalse(filename in files.keys())


    def test_sync_delete(self):
        folders, files = self.conf.list("/")
        self.assertFalse(self.remotedir in folders.keys())
        self.conf.mkdir(self.remotedir)
        self.conf.sync(self.tmppath, self.remotedir)
        folders, files = self.conf.list(self.remotedir)
        self.assertTrue(self.remotedir + "file1.txt" in files.keys())
        self.assertTrue(self.remotedir + "file2.txt" in files.keys())
        self.assertTrue(self.remotedir + "folder1/" in folders.keys())
        self.conf.delete(self.remotedir)
        folders, files = self.conf.list("/")
        self.assertFalse(self.remotedir in folders.keys())


if __name__ == '__main__':
    unittest.main()