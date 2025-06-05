#!/usr/bin/python3

from pyfakefs.fake_filesystem_unittest import TestCase
import mp3_hier_checker_v5 as hc 

def test_is_valid_mp3_filename():
    assert hc.is_valid_mp3_filename("01 - Test_Song.mp3") == True
    assert hc.is_valid_mp3_filename("01 -- Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("AA - Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("001 - Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("001 - Test_Song.MP3") == False

class HelpersTest(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_generate_list(self):
        # create fake files
        self.fs.create_file('./DirA/file1.txt')
        self.fs.create_file('./DirA/file2.txt')
        num_vio = hc.generate_list(".")
        self.assertEqual(num_vio, 3)
        
