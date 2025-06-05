#!/usr/bin/python3

import mp3_hier_checker_v5 as hc 

def test_is_valid_mp3_filename():
    assert hc.is_valid_mp3_filename("01 - Test_Song.mp3") == True
    assert hc.is_valid_mp3_filename("01 -- Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("AA - Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("001 - Test_Song.mp3") == False
    assert hc.is_valid_mp3_filename("001 - Test_Song.MP3") == False
