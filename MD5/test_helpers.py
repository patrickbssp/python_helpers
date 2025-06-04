#!/usr/bin/python3

from pyfakefs.fake_filesystem_unittest import TestCase
import helpers 

class HelpersTest(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_split_hash_filename(self):
        # Test format by md5summer with leading asterisk
        v = helpers.split_hash_filename("acbe84a180cd7fb20b097d008fdedacb *test_dir/dir2/test.txt")
        self.assertEqual(v['hash'], "acbe84a180cd7fb20b097d008fdedacb")
        self.assertEqual(v['file'], "test_dir/dir2/test.txt")

        # dito without path info
        v = helpers.split_hash_filename("dcc531fa14431e19749889e66f8c9560 *fileX.txt")
        self.assertEqual(v['hash'], "dcc531fa14431e19749889e66f8c9560")
        self.assertEqual(v['file'], "fileX.txt")

        # dito with double space
        v = helpers.split_hash_filename("dcc531fa14431e19749889e66f8c9560  *fileX.txt")
        self.assertEqual(v['hash'], "dcc531fa14431e19749889e66f8c9560")
        self.assertEqual(v['file'], "fileX.txt")

        # Test format of md5sum (no asterisk)
        v = helpers.split_hash_filename("9424c8c2c0e2234a3d9dc9d4c4a09527 ./DSC06994.JPG")
        self.assertEqual(v['hash'], "9424c8c2c0e2234a3d9dc9d4c4a09527")
        self.assertEqual(v['file'], "./DSC06994.JPG")

        # dito with double space
        v = helpers.split_hash_filename("9424c8c2c0e2234a3d9dc9d4c4a09527  ./DSC06994.JPG")
        self.assertEqual(v['hash'], "9424c8c2c0e2234a3d9dc9d4c4a09527")
        self.assertEqual(v['file'], "./DSC06994.JPG")

        # dito without path info
        v = helpers.split_hash_filename("9424c8c2c0e2234a3d9dc9d4c4a09527  DSC06994.JPG")
        self.assertEqual(v['hash'], "9424c8c2c0e2234a3d9dc9d4c4a09527")
        self.assertEqual(v['file'], "DSC06994.JPG")

    def test_with_fake_file(self):
        
        # create fake files
        self.fs.create_file('./DirA/file1.txt')
        self.fs.create_file('./DirA/file2.txt')
        self.fs.create_file('./DirA/file3.wav')
        self.fs.create_file('./DirA/DirAA/file1.txt')
        self.fs.create_file('./DirB/file1.mp3')
        self.fs.create_file('./DirB/file2.txt')
        self.fs.create_file('./DirB/file3.txt')
        self.fs.create_file('./DirB/DirBA/file1.txt')
        self.fs.create_file('./file1.txt')
        self.fs.create_file('./file2.mp3')
        self.fs.create_file('./file3.txt')
        print(self.fs)

        # Two files
        fl = helpers.create_filelist(["./DirA/file1.txt", "./DirA/file2.txt"])
        exp_list = ["./DirA/file1.txt", "./DirA/file2.txt"]
        self.assertEqual(sorted(fl), sorted(exp_list))

        # All files in current folder only
        fl = helpers.create_filelist(["."])
        exp_list = ["./file1.txt", "./file2.mp3", "./file3.txt"]
        self.assertEqual(sorted(fl), sorted(exp_list))

       # All files recursively
        fl = helpers.create_filelist(["."], recursive=True)
        exp_list = [
            './DirA/file1.txt', './DirA/file2.txt', './DirA/file3.wav', './DirA/DirAA/file1.txt',
            './DirB/file1.mp3', './DirB/file2.txt', './DirB/file3.txt', './DirB/DirBA/file1.txt',
            "./file1.txt", "./file2.mp3", "./file3.txt"]
        self.assertEqual(sorted(fl), sorted(exp_list))

        # All files recursively, plus another file
        fl = helpers.create_filelist([".", "./DirA/file1.txt"], recursive=True)
        exp_list = [
            './DirA/file1.txt', './DirA/file2.txt', './DirA/file3.wav', './DirA/DirAA/file1.txt',
            './DirB/file1.mp3', './DirB/file2.txt', './DirB/file3.txt', './DirB/DirBA/file1.txt',
            "./file1.txt", "./file2.mp3", "./file3.txt"]
        self.assertEqual(sorted(fl), sorted(exp_list))

       # All MP3 files recursively
        fl = helpers.create_filelist(["."], file_ext='mp3', recursive=True)
        exp_list = [
            './DirB/file1.mp3', "./file2.mp3"]
        self.assertEqual(sorted(fl), sorted(exp_list))


