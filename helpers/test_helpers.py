#!/bin/python3

from pyfakefs.fake_filesystem_unittest import TestCase
import helpers 
from helpers import split_hash_filename, check_ext 

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

    def test_check_ext(self):
        # Without any filters, match always
        self.assertEqual(check_ext('test_file'), True)
        self.assertEqual(check_ext('test_file.mp3'), True)
        self.assertEqual(check_ext('test_file.wav'), True)
        self.assertEqual(check_ext('test_file.mp3', ['*.mp3']), True)
        self.assertEqual(check_ext('test_file.mp3', ['*.wav', '*.mp3']), True)
        self.assertEqual(check_ext('test_file.txt', ['*.wav', '*.mp3']), False)
        self.assertEqual(check_ext('test_file.mp3', ['*.wav']), False)


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
        fl = helpers.create_filelist(["./https://github.com/pytest-dev/pyfakefsDirA/file1.txt", "./DirA/file2.txt"])
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

    def test_collect_files(self):
        from helpers import collect_files

        # create fake files
        self.fs.create_file('./DirA/file1.txt')
        self.fs.create_file('./DirA/file2.txt')
        self.fs.create_file('./DirA/file3.wav')
        self.fs.create_file('./DirA/DirAA/file1.txt')
        self.fs.create_file('./DirB/file1.mp3')
        self.fs.create_file('./DirB/file2.txt')
        self.fs.create_file('./DirB/file3.txt')
        self.fs.create_file('./DirB/DirBA/file1.txt')
        self.fs.create_file('./file2.mp3')
        self.fs.create_file('./file1.txt')
        self.fs.create_file('./file3.txt')
        print(self.fs)


        # Without any options, return all files in current directory in OS order
        fl = collect_files('.')
        exp_list = [
            'file2.mp3',
            'file1.txt',
            'file3.txt'
        ]
        self.assertEqual(len(exp_list), 3)
        self.assertEqual(fl, exp_list)

        # Without any options, return all files in current directory in OS order, relpaths
        fl = collect_files('.', use_relpath=True)
        exp_list = [
            'file2.mp3',
            'file1.txt',
            'file3.txt'
        ]
        self.assertEqual(fl, exp_list)

        # Recursive mode, return all files in current directory and below in OS order
        # Note: os.walk seems to scan files first, then directories
        fl = helpers.collect_files('.', use_recursion=True)
        exp_list = [
            'file2.mp3',
            'file1.txt',
            'file3.txt',
            'DirA/file1.txt',
            'DirA/file2.txt',
            'DirA/file3.wav',
            'DirA/DirAA/file1.txt',
            'DirB/file1.mp3',
            'DirB/file2.txt',
            'DirB/file3.txt',
            'DirB/DirBA/file1.txt'
        ]
        self.assertEqual(fl, exp_list)

       # Recursive and sorted mode, return all files in current directory and below in sorted order
        fl = helpers.collect_files('.', use_recursion=True)
        exp_list = [
            './DirA/file1.txt',
            './DirA/file2.txt',
            './DirA/file3.wav',
            './DirA/DirAA/file1.txt',
            './DirB/file1.mp3',
            './DirB/file2.txt',
            './DirB/file3.txt',
            './DirB/DirBA/file1.txt',
            './file1.txt',
            './file2.mp3',
            './file3.txt'
        ]
        self.assertEqual(sorted(fl), sorted(exp_list))

      # Recursive and sorted mode, return all MP3 and TXT files in current directory and below in sorted order
        fl = helpers.collect_files('.', use_recursion=True, use_filters=['*.mp3', '*.txt'])
        exp_list = [
            './DirA/file1.txt',
            './DirA/file2.txt',
            './DirA/DirAA/file1.txt',
            './DirB/file1.mp3',
            './DirB/file2.txt',
            './DirB/file3.txt',
            './DirB/DirBA/file1.txt',
            './file1.txt',
            './file2.mp3',
            './file3.txt'
        ]
        self.assertEqual(fl, exp_list)


        # As above, but start one level below.
        fl = helpers.collect_files('DirA', use_recursion=True, use_filters=['*.mp3', '*.txt'])
        exp_list = [
            './DirA/file1.txt',
            './DirA/file2.txt',
            './DirA/DirAA/file1.txt',
        ]
        self.assertEqual(fl, exp_list)


       # As above, but use relative paths.
        fl = helpers.collect_files('DirA', use_recursion=True, use_filters=['*.mp3', '*.txt'], use_relpath=True)
        exp_list = [
            'file1.txt',
            'file2.txt',
            'DirAA/file1.txt',
        ]
        self.assertEqual(fl, exp_list)



