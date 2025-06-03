#!/usr/bin/python3

from pyfakefs.fake_filesystem_unittest import TestCase
import helpers 

class MyTest(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

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
