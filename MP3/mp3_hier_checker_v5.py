#!/usr/bin/python3

# 10.11.2016 Ported to Python3, using mutagen
# 16.11.2016 Added list of unique artists

# rules:
# a path to an MP3 file should have following structure:
# Artist/Album/xx - Track.mp3
# where xx is the track number
# so, the directory hierarchy has 3 levels:
# level 1: (Artist)
#   - no files are allowed in this level, only directories
# level 2: (Album)
#   - no files are allowed in this level, only directories
# level 3: (Track)
#   - no directories are allowed in this level, only files
#
# rule_1a: no files are allowed in level 1
# rule_2a: no files are allowed in level 2
# rule_3a: no directories are allowed in level 3
# rule_3b: filenames must have format 'xx - Trackname.mp3'
#
# Test cases:
#
# - Track number containing letter O instead of digit 0
# - Double spaces
# - File suffix mixed or all upper-case
# - Empty Artist folder
# - Empty Album folder
# - Files in Artist folder
# - Non-MP3-Files in any folder
#
# Due to file/folder naming requirements on various OSes, following rules should be observed:
# - Do not use trailing dots for folders (problematic on Windows)
# - Do not use leading dots for folders (problematic on Unix (hidden folders))
#
# Homoglyph replacement (to escape characters with special meaning to filesystems
# / (slash) -> U+29F8   ⧸   e2 a7 b8  BIG SOLIDUS     (page Misc. Mathematical Symbols-B)
# / (slash) -> U+2215   ∕   e2 88 95  DIVISION SLASH) (page Mathematical Operators)
# : (colon) -> U+2236   ∶   e2 88 b6  RATIO           (page Mathematical Operators)

import sys
import re
import glob
import os.path
import pathlib
import csv
import argparse

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers, extract_tags

enable_report_substitutions = True

substitutions_done = set()

num_files = 0
num_mp3 = 0

class ViolationCounter:
    _num_violations = 0
    _violations = []

    def add_violation(self, text):
        self._violations.append(text)

    def report_violations(self):
        print(f'num. violations: {self.get_violation_cnt()}')
        for v in self._violations:
            print(v)

    def get_violation_cnt(self):
        return len(self._violations)

violations = ViolationCounter()

field_names = [
    'f_artist',         # artist (from filename)
    'f_album',          # album (from filename)
    'f_title',          # title (from filename)
    'f_track',          # track number (from filename)
    'f_type',           # file type (from filename)
    't_artist',         # artist (from tag, TPE1)
    't_album_artist',   # album artist (from tag, TPE2)
    't_album',          # album (from tag, TALB)
    't_title',          # title (from tag, TIT2)
    't_track',          # track number (from tag, TRCK)
]

class LengthTracker:
    
    file_longest = ''
    file_shortest = ''
    stats_max={}
    stats_min={}
    for f in field_names:
        stats_max[f] = None
        stats_min[f] = None

    def check_length(self, full_path):
        l = len(full_path)
    
        if self.file_shortest and l < len(self.file_shortest) or not self.file_shortest:
            self.file_shortest = full_path

        if self.file_longest and l > len(self.file_longest) or not self.file_longest:
            self.file_longest = full_path

    def check_tag(self, k, v):
        
        l = len(v)
        if self.stats_max[k] and l > len(self.stats_max[k]) or not self.stats_max[k]:
            self.stats_max[k] = v
        if self.stats_min[k] and l < len(self.stats_min[k]) or not self.stats_min[k]:
            self.stats_min[k] = v

len_tracker = LengthTracker()


unique_artists = set()
unique_albums = set()

### Enable/disable debugging (True/False)
debug = False

report_mismatch_flags = {
    'artist'        : True,
    'album_artist'  : True,
    'album'         : True,
    'track'         : True,     # Don't change this entry!
    'title'         : False
}


substitutions = {
    'artist' : {
        ### List combinations of artist names here, to be substituted in matching checks.
        ###   key:   Simplified artist name (as used in folder names)
        ###   value: Full artist names (as used in ID3 tags)
        ### This helps to white-list artists which have non-representable characters and/or long names
        ### not suitable for the filesystems.
        ### Example:    "Bahntier"  : ":Bahntier//",

#        "à;Grumh"                           : "à;Grumh...",
        "Bahntier"                          : ":Bahntier//",
        "Ditto - Destroyer"                 : "Ditto ≠ Destroyer",
        "Howden & Wakeford"                 : "Howden/Wakeford",
        "ProTech"                           : "Pro>Tech",
        "Sixth Comm - Mother Destruction"   : "Sixth Comm / Mother Destruction",
        "System-Eyes"                       : r"System\\Eyes",
        "Test Dept. - Brith Gof"            : "Test Dept. / Brith Gof",
    },
    'album' : {

        ### List combinations of album names here, to be substituted in matching checks.
        ### Rules and rationale are the same as for artists.
        ### Example:    "Terminator 2 - Judgment Day - O.S.T" : "Terminator 2: Judgment Day - Original Motion Picture Soundtrack",

        "Acoustic - La Ferrière-Harang - Bérigny, Normandie, France, 2011-2013"     : "Acoustic - La Ferrière-Harang/Bérigny, Normandie, France, 2011-2013",
        "Aus Der Welt (The Collective Works 2000 - 2003)"                           : "Aus Der Welt / Seduction Of Madness / Death, Dumb And Blind (The Collective Works 2000 - 2003)",
        "Bellum, Sacrum Bellum"                                                     : "Bellum, Sacrum Bellum!?",
        "Construct Destruct"                                                        : "Construct >< Destruct",
        "Crocodile Dundee - Original Motion Picture Score"                          : "\"Crocodile\" Dundee - Original Motion Picture Score",
        "Der Ring Des Nibelungen (Excerpts)"                                        : " Der Ring Des Nibelungen (Excerpts/Extraits/Auszüge, Deborah Polaski, Chicago Symphony Orchestra, Daniel Barenboim)",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD01)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD01: Hast Du Mich Vermisst? (Der Schwarze Schmetterling I))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD02)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD02: :Duett (Der Schwarze Schmetterling II))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD03)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD03: Weltunter (Der Schwarze Schmetterling III))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD04)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD04: Aus Der Tiefe (Der Schwarze Schmetterling IV))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD05)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD05: Requiembryo (Der Schwarze Schmetterling V) (CD1))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD06)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD06: Requiembryo (Der Schwarze Schmetterling V) (CD2))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD07)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD07: Weltunter (Komm Zu Mir) / Stille Der Nacht (Ein Weihnachtsmärchen) (Singles 2003))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD08)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD08: Ich Will Brennen (Single 2004) / Werben (Single 2006))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD09)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD09: Ich Bin Ein Wahrer Satan (Vier Singles 2006))",
        "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD10)"              : "Der Komplette Schwarze Schmetterling Zyklus (I Bis V) (CD10: Ich Bin Ein Wahrer Satan (Vier Singles 2006))",
        "Der Ring Des Nibelungen (Excerpts)"                        : "Der Ring Des Nibelungen (Excerpts/Extraits/Auszüge, Deborah Polaski, Chicago Symphony Orchestra, Daniel Barenboim)",
        "Es reiten die Toten so schnell"                            : "Es reiten die Toten so schnell (Or: The Vampyre Sucking At His Own Vein)",
        "German Mystic Sound Sampler Vol. II"                       : "German Mystic Sound Sampler II",
        "Götterdämmerung (Pierre Boulez) (CD1)"                     : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD1)",
        "Götterdämmerung (Pierre Boulez) (CD2)"                 : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD2)",
        "Götterdämmerung (Pierre Boulez) (CD3)"                 : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD3)",
        "Götterdämmerung (Pierre Boulez) (CD4)"                 : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD4)",
        "In Case You Didn't Feel Like Showing Up (Original Album Series)"   : "In Case You Didn't Feel Like Showing Up (Live) (Original Album Series)",
        "In Flimmernder Nacht"                       : "In Flimmernder Nacht ...",
        "Join The Dots - B-Sides & Rarities (CD1)"  : "Join The Dots - B-Sides & Rarities (CD1: 1978>1987)",
        "Join The Dots - B-Sides & Rarities (CD2)"  : "Join The Dots - B-Sides & Rarities (CD2: 1987>1992)",
        "Join The Dots - B-Sides & Rarities (CD3)"  : "Join The Dots - B-Sides & Rarities (CD3: 1992>1996)",
        "Join The Dots - B-Sides & Rarities (CD4)"  : "Join The Dots - B-Sides & Rarities (CD4: 1996>2001)",
        "Laugh - I Nearly Bought One!"              : "Laugh? I Nearly Bought One!",
        "Left Of The Dial (CD1)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD1)",
        "Left Of The Dial (CD2)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD2)",
        "Left Of The Dial (CD3)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD3)",
        "Left Of The Dial (CD4)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD4)",
        "Love Poems For Dying Children... Act III"              : "Love Poems For Dying Children... Act III: Winter And The Broken Angel",
        "Meeresrauschen Mit Möwen- Und Vogelgezwitscher"        : "Meeresrauschen Mit Möwen- Und Vogelgezwitscher Und Delphin- Und Walgesängen",
        "Mellon Collie And The Infinite Sadness (CD1)"          : "Mellon Collie And The Infinite Sadness - Dawn To Dusk",
        "Mellon Collie And The Infinite Sadness (CD2)"          : "Mellon Collie And The Infinite Sadness - Twilight To Starlight",
        "Music From Twin Peaks - Fire Walk With Me"             : "Music From The Motion Picture Soundtrack Twin Peaks - Fire Walk With Me",
        "Musica Reservata (CD2 - Bonus CD)"                     : "Musica Reservata (CD2: Bonus CD With Rare, Live And Unreleased Tracks)",
        "Nightglory (Deluxe Edition) (CD1)"                     : "Nightglory (Deluxe Edition) (CD1: Nightglory)",
        "Nightglory (Deluxe Edition) (CD2)"                     : "Nightglory (Deluxe Edition) (CD2: Whispered Triumph Of Death (Nightglory Spin-Off))",
        "Odyssey Europa (Limited Edition) (CD1)"                : "Odyssey Europa (4 CD Special Limited Edition) (CD1)",
        "Odyssey Europa (Limited Edition) (CD2)"                : "Odyssey Europa (4 CD Special Limited Edition) (CD2)",
        "Odyssey Europa (Limited Edition) (CD3)"                : "Odyssey Europa (4 CD Special Limited Edition) (CD3)",
        "Odyssey Europa (Limited Edition) (CD4)"                : "Odyssey Europa (4 CD Special Limited Edition) (CD4)",
        "Paradise"                                              : "Paradise... ?",
        "Pictures From Eternity (Twilight Records)"             : "Pictures From Eternity - Bilder Aus Der Ewigkeit (Twilight Records)",
        "Playlist - The Very Best Of Survivor"                  : "Playlist: The Very Best Of Survivor",
        "Prince Of Darkness - O.S.T. (CD1)"                     : "Prince Of Darkness - Complete Original Motion Picture Soundtrack (Limited Edition) (CD1)",
        "Prince Of Darkness - O.S.T. (CD2)"                     : "Prince Of Darkness - Complete Original Motion Picture Soundtrack (Limited Edition) (CD2)",
        "Riding The Crest Of The Frozen Wave"                   : "Riding The Crest Of The Frozen Wave - A Tribute To The Frozen Autumn",
        "Scatology (Remastered)"                                    : "Stevø, Pay Us What You Owe Us! Volume One - Scatology - Remastered", 
        "Sin Pecado (Original Album Collection)"                                    : "Sin / Pecado (Original Album Collection)",
        "The Dark Box (CD1)"                                                        : "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD1)",
        "The Dark Box (CD2)"                                                        : "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD2)",
        "The Dark Box (CD3)"                                                        : "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD3)",
        "The Dark Box (CD4)"                                                        : "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD4)",
        "The Gothic Grotesque & Elektro Bizarre (Promo Edition)"                    : "The Gothic Grotesque & Elektro Bizarre - Trisol Compilation 1 (Promo Edition)",
        "The Hobbit - The Battle Of The Five Armies - OST (Special Edition) (CD1)"  : "The Hobbit - The Battle Of The Five Armies - Original Motion Picture Soundtrack (Special Edition) (CD1)",
        "The Hobbit - The Battle Of The Five Armies - OST (Special Edition) (CD2)"  : "The Hobbit - The Battle Of The Five Armies - Original Motion Picture Soundtrack (Special Edition) (CD2)",
        "The Hunt For Red October - Original Soundtrack"    : "The Hunt For Red October - Music From The Original Motion Picture Soundtrack",
        "The Infinite (Promo)"                              : "... The Infinite (Promo)",
        "The Last Embrace"                                  : "... The Last Embrace",
        "The Most Spectacular Synthesizer Hits"             : "The Most Spectacular Synthesizer Hits Of Vangelis, Jean-Michel Jarre & Jan Hammer Played By Star Inc.",
        "The Naked Gun 21-2 - The Smell Of Fear - O.S.T"    : "The Naked Gun 21/2: The Smell Of Fear - Music From The Motion Picture",
        "The Triumph Of Light"                              : "The Triumph Of Light... And Thy Thirteen Shadows Of Love",
        "Wenches, Wytches And Vampyres - The Very Best Of Two Witches"  : "Wenches, Wytches And Vampyres - The Very Best Of Two Witches 1987-1999",
        "What Sweet Music They Make - The Best Of (CD1)"    : "Thee Vampire Guild - What Sweet Music They Make - The Best Of (CD1)",
        "What Sweet Music They Make - The Best Of (CD2)"    : "Thee Vampire Guild - What Sweet Music They Make - The Best Of (CD2)",
        "What Sweet Music They Make Vol. 2"                 : "What Sweet Music They Make - Thee Vampire Guild Compilation Vol. 2",
        "With A Million Tear-Stained Memories (CD1)"        : "With A Million Tear-Stained Memories (CD1) (Vocal Tracks)",
        "With A Million Tear-Stained Memories (CD2)"        : "With A Million Tear-Stained Memories (CD2) (Instrumental Tracks)",
        "Works & Passion 1955 - 2000 (CD1)"                 : "Works & Passion 1955 - 2000 (CD1: The Feetwarmers - The Quartet - Paul Nero - Motherhood)",
        "Works & Passion 1955 - 2000 (CD2)"                 : "Works & Passion 1955 - 2000 (CD2: The Soloist - The Composer)",
        "Works & Passion 1955 - 2000 (CD3)"                 : "Works & Passion 1955 - 2000 (CD3: Passport 1971 - 1980)",
        "Works & Passion 1955 - 2000 (CD4)"                 : "Works & Passion 1955 - 2000 (CD4: Passport 1980 - 2000)",
        "Zwischenfall - From The 80's To The 90's Vol. 2 (CD1)" : "Zwischenfall Vol. 2 (CD1)",
        "Zwischenfall - From The 80's To The 90's Vol. 2 (CD2)" : "Zwischenfall Vol. 2 (CD2)",
    },
    'album_artist' : {
                ### List Album Artist/Album combos here, for which Album Artist check should be skipped
                ### This is useful for Albums with multiple Artists, which are no Compilations, where
                ### Album Artist would be Various Artists.
                "Solitary Experiments" : ["Phenomena (CD2: Hysteria)"],
                "Klaus Doldinger" : [
                        "Works & Passion 1955 - 2000 (CD1: The Feetwarmers - The Quartet - Paul Nero - Motherhood)",
                        "Works & Passion 1955 - 2000 (CD2: The Soloist - The Composer)",
                        "Works & Passion 1955 - 2000 (CD3: Passport 1971 - 1980)",
                        "Works & Passion 1955 - 2000 (CD4: Passport 1980 - 2000)"
                        ],
                "Queen" : [
                        "Greatest Hits III (2011 Digital Remaster)"
                    ],
                "Hekate" : [
                        "Taurus (Gesammelte Werke 1992-2011)"
                    ],
                "Kiss" : [
                        "God Gave Rock & Roll To You II"
                    ],
                "The Dust Of Basement" : [
                        "Meridian (CD2)",
                        "Awakening The Oceans (CD2)"
                    ],
                "Matthias Schuster" : [
                        "Atemlos"
                    ],
                "Sara Noxx & Mark Benecke" : [
                        "Where The Wild Roses Grow (Re-Mixxed)"
                    ],
    }
}

### files
unique_artists_file = "unique_artists.txt"
unique_albums_file = "unique_albums.txt"
substitutions_file = "substitutions.txt"

def my_print(str):
    """
        Wrapper to use alternate stdout handle capable of UTF-8 irregarding of environment.
    """
    if 'uni_stdout' in globals():
        print(str, file=uni_stdout)

def tag_from_fileinfo(fi, field_names):
    # Create a dict with keys from field_names and values from fileinfo
    tag = {t : fi[t] for t in field_names}
    return tag

def parse_file(top_dir, full_path, md5_fh):

    path_rel = pathlib.PurePath(full_path).relative_to(top_dir)

    if len(path_rel.parts) != 3:
        my_print(f'violation: invalid file: {full_path}')
        return 1, None

    fname = path_rel.parts[2]
    if not is_valid_mp3_filename(fname):
        violations.add_violation(f"violation: rule_3b: filenames must have format 'xx - Trackname.mp3', but got: {path_rel.parts[-3:]}")
        return 1, None
    
    md5 = helpers.file_md5(full_path)
    str = f'{md5}  {path_rel}\n'
    if md5_fh:
        md5_fh.write(str)
    else:
        print(str, end='')

    return 0, None


def extract_tags_to_csv(top_dir, csv_file):
    files = []
    # compile file list, note: glob will also catch folders with dots somewhere in the name
    for filename in glob.glob(top_dir+'/**/*.*', recursive=True):
        _, ext = os.path.splitext(filename)
        if ext in ['.mp3', '.flac']:
            files.append(filename)
    # 
    if len(files) == 0:
        print('No files found')
        return

    ### Open CSV file
    with open(csv_file, mode='w+', encoding='utf-8', errors='surrogateescape') as csv_fh:
        csv_wh = csv.DictWriter(csv_fh, fieldnames=field_names, dialect='mp3_csv')
        csv_wh.writeheader()

        for full_path in files:
            fi = extract_tags.FileInfo(full_path)
            tag = tag_from_fileinfo(fi, field_names)
            csv_wh.writerow(tag)

def report_mismatch(fname, item, f_item, t_item):
    violations.add_violation('Mismatch in {}, file: {} tag: {} (file: {})'.format(item, f_item, t_item, fname))

def report_substitution(reason, orig, sub):
    if enable_report_substitutions:
        sub = 'Replaced {}: {} with {}'.format(reason, orig, sub)
        substitutions_done.add(sub)

def is_mismatch(f_item, t_item, item):
    return True if f_item != t_item and report_mismatch_flags[item] else False

def remove_dots_and_spaces(s):
    '''Remove leading and trailing dots and spaces from string'''
    return s.strip(' .')

def match_artist(tag):
    """
    (Try to) match artist.

    Artist may not match exactly due to folder name restrictions
    (trailing dots, colons, etc.).
    """

    f_artist = tag['f_artist']
    t_artist = tag['t_artist']

    if not report_mismatch_flags['artist']:
        ### Check disabled
        return True

    if std_repl('AR', f_artist, t_artist):
        return True

    ### Check, whether there is a substitution available
    if f_artist in substitutions['artist']:
        if t_artist == substitutions['artist'][f_artist]:
            ### Substitute matches
            return True

    ### Still not matching -> error
    return False

def match_album_artist(tag):
    """
    (Try to) match album artist.

    Album artist is matched against artist, both from tag. Album artist may differ for
    compilations or if field is missing.
    """

    t_artist = tag['t_artist']
    t_album_artist = tag['t_album_artist']
    t_album = tag['t_album']

    if not report_mismatch_flags['album_artist']:
        ### Check disabled
        return True

    if t_artist == t_album_artist:
        ### Perfect match
        return True

    if t_album_artist in ['Various Artists', '']:
        ### Compilation
        return True

    ### Check, whether there is a substitution available
    if t_album_artist in substitutions['album_artist']:
        if t_album in substitutions['album_artist'][t_album_artist]:
            ### Substitute matches
            return True


    ### Still not matching -> error
    return False

def std_repl(cat, f_item, t_item):
    """
        Apply standard replacements:

        cat:    Category:
            AR  Artist
            AA  Album Artist
            AL  Album
    """

    substitutions = {
        "AR" : {
            ### Note: first entries for ':' and '/' are homoglyps!
            ':' : ['∶'],
            '/' : ['⁄'],
            '?' : [''],
        },
        "AL" : {
            ### Note: first entries for ':' and '/' are homoglyps!
            ':' : ['∶'],
            '/' : ['⁄'],
            '?' : [''],
            '>' : ['-'],
            '=' : ['-'],
        },
    }

    if f_item == t_item:
        ### Perfect match
        return True

    ### Single substitution
    if cat in substitutions:
        subs = substitutions[cat]
        for i,v in enumerate(subs):
            for sub in subs[v]:
                if f_item == t_item.replace(v, sub):
                    report_substitution(f'{cat}{i}', t_item, f_item)
                    return True

    ### Multiple substitutions
    t_item_mod = t_item
    if cat in substitutions:
        subs = substitutions[cat]
        for i,v in enumerate(subs):
            for sub in subs[v]:
                t_item_mod = t_item_mod.replace(v, sub)
                if f_item == t_item_mod:
                    report_substitution(f'{cat}{i*10}', t_item_mod, f_item)
                    return True

    if cat in ['AL', 'AR']:

        s = remove_dots_and_spaces(t_item_mod)
        if s == f_item:
            return True

    return False

def match_album(tag, item):
    """
    (Try to) match album.

    Album may not match exactly due to folder name restrictions
    (trailing dots, colons, etc.).
    """

    f_album = tag['f_album']
    t_album = tag['t_album']

    if not report_mismatch_flags[item]:
        ### Check disabled
        return True

    if std_repl('AL', f_album, t_album):
        return True

    ### Check, whether there is a substitution available
    if f_album in substitutions['album']:
        if t_album == substitutions[item][f_album]:
            ### Substitute matches
            return True

    ### Still not matching -> error
    return False

def match_title(tag, item):
    """
    (Try to) match title.

    Album may not match exactly due to folder name restrictions
    (trailing dots, colons, etc.).
    """

    f_title = tag['f_title']
    t_title = tag['t_title']

    if not report_mismatch_flags[item]:
        ### Check disabled
        return True

    if f_title == t_title:
        ### Perfect match
        return True

    if f_title == t_title.replace('/', '-').replace(':', '').replace('?', ''):
        ### Standard replacement
        return True

    if f_title == t_title.replace('/', ' - ').replace(':', ' -').replace('"', ''):
        ### Standard replacement
        return True

    if f_title == t_title.replace(':', '-').replace('"', '\''):
        ### Standard replacement
        return True

    ### Still not matching -> error
    return False

def check_cdm(str):
    """
        Check for combining diacritical marks, i.e. accented characters composed of base
        character plus mark.
        For example, an 'í' can be represented as
        a) Single char   (2 bytes in UTF-8): 0xc3 0xad      -> LATIN SMALL LETTER I WITH ACUTE
        b) Composed char (3 bytes in UTF-8): 0x69 0xcc 0x81 -> LATIN SMALL LETTER I plus COMBINING ACUTE ACCENT
    """
    chars = [b'\xcc', b'\xcd']

    ba = str.encode('utf-8')
    for i,_ in enumerate(ba):
        for c in chars:
            d = (ba[i]).to_bytes(1, 'big')
            if d == c:
                e = ba[i-1:i+2].decode('utf-8')
                return e

# Extract track number and title from filename
# Returns either a tuple of track and title or None
def get_track_title(fname):
    # Title must not contain leading or trailing white-space, but may contain spaces
    # in between. Also, title may contain a single character.
    m = re.match(r"^(\d\d) - (\S[\S ]*\S|\S)\.mp3", fname)
    if m and len(m.groups()) == 2:
        return m.group(1), m.group(2)

# check, whether MP3 filename convention is maintained 
def is_valid_mp3_filename(filename):
    return True if get_track_title(filename) else False


def check_tag(tag):
    """
        Check file for errors or inconsistencies.

        Return value: Tag entry if no errors occured; None otherwise
    """
    if tag['f_type'] == 'mp3':
        full_path = f"{tag['f_artist']}/{tag['f_album']}/{tag['f_track']} - {tag['f_title']}.mp3"
    elif tag['f_type'] == 'flac':
        # If filename does not contain title, just take the one from the tag
        title = tag['f_title'] if len(tag['f_title']) > 0 else tag['t_title']
        full_path = f"{tag['f_artist']}/{tag['f_album']}/{tag['f_track']} - {title}.flac"

    len_tracker.check_length(full_path)

    ### Scan for unwanted combining diacritical marks
    for k,v in tag.items():

        len_tracker.check_tag(k, v)
        c = check_cdm(v)
        if c:
            my_print(f'CDM {c} found: {k} in {full_path}')

    ### Check tags

    unique_artists.add(tag['t_artist'])
    unique_albums.add(tag['t_album'])

    ### Track number must match exactly. No excuses...
    if is_mismatch(tag['f_track'], tag['t_track'], 'track'):
        report_mismatch(full_path, "Track number", tag['f_track'], tag['t_track'])

    ### Artist may not match exactly due to folder name restrictions
    if not match_artist(tag):
        report_mismatch(full_path, "Artist", tag['f_artist'], tag['t_artist'])

    ### Album artist may not match exactly due to compilations/missing fields
    if not match_album_artist(tag):
        report_mismatch(full_path, "Album artist", tag['f_artist'], tag['t_album_artist'])

    if not match_album(tag, 'album'):
        report_mismatch(full_path, "Album", tag['f_album'], tag['t_album'])

    if not match_title(tag, 'title'):
        report_mismatch(full_path, "Title", tag['f_title'], tag['t_title'])
    return tag

def parse_dir(top_dir, md5_fh):
    num_files = 0
    num_mp3 = 0

    for dirpath, dirnames, filenames in os.walk(top_dir):
        dirnames.sort()
        filenames.sort()
        if (len(dirnames) == 0) and (len(filenames) == 0):
            violations.add_violation(f"violation: rule_xx: empty folder detected: {dirpath}")

        ### then, iterate over files
        for fname in filenames:
            num_files += 1
            p = pathlib.PurePath(dirpath)
            if len(p.parts) == 0:
                violations.add_violation(f"violation: rule_1a: no files are allowed in level 1: {fname}")
            elif len(p.parts) == 1:
                # TODO check whether this should not be rule_1b / level 2
                violations.add_violation(f"violation: rule_1a: no files are allowed in level 1: {fname}")
            else:
                _, tag = parse_file(top_dir, os.path.join(dirpath, fname), md5_fh)
                if tag:
                    num_mp3 += 1
    return num_files, num_mp3

# Generate report.
# Depending on the options chosen, either MD5 hashes are calculated, CSV entries
# are generated, or both
# This function returns the number of violations for testability
def generate_list(top_dir, md5_file=None):

    md5_fh = None

    ### Open MD5 file
    if md5_file:
        md5_fh = open(md5_file, mode='w+', encoding='utf-8')

    num_files, num_mp3 = parse_dir(str(pathlib.PurePath(top_dir)), md5_fh)

    report = f'''-------------------------------------------------------------\n
        Top folder: {top_dir}\n
        {num_files} file(s) checked\n
        {num_mp3} MP3 file(s) found\n
        {violations.get_violation_cnt()} violation(s) found\n'''

    violations.report_violations()

    if md5_file:
        md5_fh.write(report)
    if md5_file:
        md5_fh.close()

    return violations.get_violation_cnt()

def analyse_csv(csv_file):
    ### Open and parse CSV file
    with open(csv_file, mode='r', encoding='utf-8', errors='surrogateescape') as f:
        reader = csv.DictReader(f, fieldnames=field_names, dialect='mp3_csv')
        for row in reader:
            if reader.line_num > 1:
                print(row)
                check_tag(row)

    ### Dump unique artists to file
    with open(unique_artists_file, "w", encoding='utf8') as f:
        for artist in sorted(unique_artists):
            f.write(f'{artist}\n')
    
    ### Dump unique albums to file
    with open(unique_albums_file, "w", encoding='utf8') as f:
        for album in sorted(unique_albums):
            f.write(f'{album}\n')

    if enable_report_substitutions:
        with open(substitutions_file, "w", encoding='utf8') as f:
            for line in sorted(substitutions_done):
                f.write(f'{line}\n')

    violations.report_violations()
    my_print('----------------------------------------------------')
    my_print(f'Path (max): {len(len_tracker.file_longest)} {len_tracker.file_longest}')
    my_print('Artist (max):')
    my_print(f'  Tag:  {len(len_tracker.stats_max['t_artist']):3d}   {len_tracker.stats_max['t_artist']}')
    my_print(f'  File: {len(len_tracker.stats_max['f_artist']):3d}   {len_tracker.stats_max['f_artist']}')
    my_print('Album (max):')
    my_print(f'  Tag:  {len(len_tracker.stats_max['t_album']):3d}   {len_tracker.stats_max['t_album']}')
    my_print(f'  File: {len(len_tracker.stats_max['f_album']):3d}   {len_tracker.stats_max['f_album']}')
    my_print('Title (max):')
    my_print(f'  Tag:  {len(len_tracker.stats_max['t_title']):3d}   {len_tracker.stats_max['t_title']}')
    my_print(f'  File: {len(len_tracker.stats_max['f_title']):3d}   {len_tracker.stats_max['f_title']}')

def main():
    global uni_stdout

    ### Register dialect
    csv.register_dialect('mp3_csv', delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')

    ### Open another filehandle to stdout supporting UTF8 to prevent unicode issues with print()
    ### Note:   These problems may be only present when running the script locally and work flawless
    ###         over SSH.
    uni_stdout = open(1, 'w', encoding='utf-8', closefd=False)

    parser = argparse.ArgumentParser(

        usage = """
        -m DIR [MD5_FILE]         Check file hierarchy, naming rules etc. starting from DIR,
                                  and dumping MD5 hashes to stdout.
                                  If MD5_FILE is provided, MD5 hashes are dumped to this file
                                  instead of stdout.
        -e DIR CSV_FILE           Extract MP3 tags starting from DIR and dump them to CSV_FILE.
        -c DIR MD5_FILE CSV_FILE  Combines options -m and -e.
        -a CSV_FILE               Analyse CSV file.
        """
    )

    # Create a mutually exclusive group
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-m', nargs='+', help='Check file hierarchy, naming rules etc. and dump MD5 hashes.')
    group.add_argument('-e', nargs=2, help='Extract MP3 tags starting from DIR and dump tags to CSV_FILE.')
    group.add_argument('-c', nargs=3, help='Combines options -m and -e.')
    group.add_argument('-a', nargs=1, help='Analyse CSV file.')
    args = parser.parse_args()

    if args.m and (1 <= len(args.m) <= 2):
        if len(args.m) == 2:
            md5_file = args.m[1]
        else:
            md5_file = None
        generate_list(args.m[0], md5_file=md5_file)
    elif args.e:
        extract_tags_to_csv(args.e[0], csv_file=args.e[1])
    elif args.c:
        generate_list(args.c[0], md5_file=args.c[1])
        extract_tags_to_csv(args.c[0], csv_file=args.c[2])
    elif args.a:
        analyse_csv(args.a[0])

    sys.exit(0)

if __name__ == '__main__':
    main()

