#!/usr/bin/python3

from pyfakefs.fake_filesystem_unittest import TestCase
import mp3_hier_checker_v5 as hc 

def test_is_valid_mp3_filename():
    assert hc.is_valid_mp3_filename("01 - Test_Song.mp3") == True
    assert hc.is_valid_mp3_filename("01 - Test Song.mp3") == True
    assert hc.is_valid_mp3_filename("01 - T.mp3") == True
    assert hc.is_valid_mp3_filename("01 -  Test Song.mp3") == False # leading space
    assert hc.is_valid_mp3_filename("01 - Test Song .mp3") == False # trailing space
    assert hc.is_valid_mp3_filename("01 -- Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("AA - Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("001 - Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("001 - Test_Song.MP3") == False

def test_remove_dots_and_spaces():
    assert hc.remove_dots_and_spaces("Test") == "Test"
    assert hc.remove_dots_and_spaces("!Test") == "!Test"
    assert hc.remove_dots_and_spaces("Test!") == "Test!"
    assert hc.remove_dots_and_spaces(".Test") == "Test"
    assert hc.remove_dots_and_spaces("..Test.") == "Test"
    assert hc.remove_dots_and_spaces("Test.") == "Test"
    assert hc.remove_dots_and_spaces(".Test..") == "Test"
    assert hc.remove_dots_and_spaces(" .Test") == "Test"
    assert hc.remove_dots_and_spaces(". Test") == "Test"
    assert hc.remove_dots_and_spaces(". Test .") == "Test"
    assert hc.remove_dots_and_spaces("Test. .") == "Test"

class HelpersTest(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_generate_list(self):
        # create fake files
        self.fs.create_file('./Artist_A/Album_A/01 - Song.mp3')
        self.fs.create_file('./Artist_A/Album_A/02 - Song.mp3')
        self.fs.create_file('./Artist_A/Album_B/01 - Song.mp3')
        self.fs.create_file('./Artist_B/Album_A/01 - Song.mp3')
        self.fs.create_file('./Artist_B/Album_A/02 - Song.mp3')
        self.fs.create_file('./Artist_B/Album_A/02 Song.mp3')   # 1 viol. (misnamed track)
        self.fs.create_dir('./Artist_C/')          # 1 viol. (empty artist)
        self.fs.create_dir('./Artist_D/Album_A/')   # 1 viol. (empty album)
        self.fs.create_file('./test.txt')           # 1 viol. (file in level 1)
        self.fs.create_file('./Artist_A/test.txt')  # 1 viol. (file in level 2)
        print(self.fs)
        num_vio = hc.generate_list(".")
        # pyfakefs will create a folder ./tmp which will trigger one violation
        self.assertEqual(num_vio, 6)
        
