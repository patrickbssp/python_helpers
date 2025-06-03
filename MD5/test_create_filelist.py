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

		fl = helpers.create_filelist("./DirA/file1.txt ./DirA/file2.txt")
		self.assertEqual(fl, '')
		print(fl)

#		self.assertEqual(content, 'hello wonnrld')
