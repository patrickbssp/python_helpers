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
import os.path
import shlex
import subprocess
import pathlib
import mutagen
import csv

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers

file_shortest = None
file_longest = None

stats_max={}
stats_min={}

enable_report_substitutions = True

substitutions_done = set()

num_files = 0
num_mp3 = 0
num_violations = 0

field_names = [
    'f_artist',         # artist (from filename)
    'f_album',          # album (from filename)
    'f_title',          # title (from filename)
    'f_track',          # track number (from filename)
    't_artist',         # artist (from tag, TPE1)
    't_album_artist',   # album artist (from tag, TPE2)
    't_album',          # album (from tag, TALB)
    't_title',          # title (from tag, TIT2)
    't_track',          # track number (from tag, TRCK)
]

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

tag_mapping = {
    'TRCK'  : 't_track',
    'TALB'  : 't_album',
    'TPE1'  : 't_artist',
    'TPE2'  : 't_album_artist',
    'TIT2'  : 't_title'
}

substitutions = {
    'artist' : {
        ### List combinations of artist names here, to be substituted in matching checks.
        ###   key:   Simplified artist name (as used in folder names)
        ###   value: Full artist names (as used in ID3 tags)
        ### This helps to white-list artists which have non-representable characters and/or long names
        ### not suitable for the filesystems.
        ### Example:    "Bahntier"  : ":Bahntier//",

        "à;Grumh"                           : "à;Grumh...",
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

        "Terminator 2 - Judgment Day - O.S.T"                                       : "Terminator 2: Judgment Day - Original Motion Picture Soundtrack",
        "Acoustic - La Ferrière-Harang - Bérigny, Normandie, France, 2011-2013"     : "Acoustic - La Ferrière-Harang/Bérigny, Normandie, France, 2011-2013",
        "A Guide To The Legendary Pink Dots - Vol. 1"                               : "A Guide To The Legendary Pink Dots - Vol. 1 The Best Ballads",
        "An Entire Wardrobe Of Doubt And Uncertainty (CD1 - Album)"                 : "An Entire Wardrobe Of Doubt And Uncertainty (CD1: Album)",
        "An Entire Wardrobe Of Doubt And Uncertainty (CD2 - Commentary)"            : "An Entire Wardrobe Of Doubt And Uncertainty (CD2: Patented Deadfly Ensemble Double Album Commentary)",
        "Aus Der Welt (The Collective Works 2000 - 2003)"                           : "Aus Der Welt / Seduction Of Madness / Death, Dumb And Blind (The Collective Works 2000 - 2003)",
        "Bellum, Sacrum Bellum"                                                     : "Bellum, Sacrum Bellum!?",
        "Blade Runner Trilogy (CD2) - BR Prev. Unrel. & Bonus Material"             : "Blade Runner Trilogy (CD2) - Blade Runner Previously Unreleased & Bonus Material",
        "Blinded By The Light - The Very Best Of"                                   : "Blinded By The Light - The Very Best Of Manfred Mann's Earth Band",
        "Celebrant 2004-05 - Der Mittelalterliche Klangkörper Zum WGT"              : "Celebrant 2004/05 - Der Mittelalterliche Klangkörper Zum Wave-Gotik-Treffen",
        "Cold Hands Seduction Vol. 36 (2004-04) (CD2)"                              : "Cold Hands Seduction Vol. 36 (2004-04) (CD2) (Mittelaltermusik-Special Vol. II)", 
        "Cold Hands Seduction Vol. 46 (2005-03) (CD2)"                              : "Cold Hands Seduction Vol. 46 (2005-03) (CD2) (Mittelalter-Special Vol. 3)",
        "Conan The Barbarian - Original Soundtrack (Re-Release)"                    : "Conan The Barbarian - Original Motion Picture Soundtrack (Re-Release)",
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
        "Die Aesthetik Der Herrschaftsfreiheit (CD1 - Aufbruch)"    : "Die Aesthetik Der Herrschaftsfreiheit (CD1: Aufbruch Oder A Cross Of Wheat)",
        "Die Aesthetik Der Herrschaftsfreiheit (CD2 - Aufruhr)"     : "Die Aesthetik Der Herrschaftsfreiheit (CD2: Aufruhr Oder A Cross Of Fire)",
        "Die Aesthetik Der Herrschaftsfreiheit (CD3 - Aufgabe)"     : "Die Aesthetik Der Herrschaftsfreiheit (CD3: Aufgabe Oder A Cross Of Flowers)",
        "Die Flut (CD1)"                                            : "Die Flut - Die Benefiz Compilation Der Darkwave- Und Elektroszene (CD1)",
        "Die Flut (CD2)"                                            : "Die Flut - Die Benefiz Compilation Der Darkwave- Und Elektroszene (CD2)",
        "Der Ring Des Nibelungen (Excerpts)"                        : "Der Ring Des Nibelungen (Excerpts/Extraits/Auszüge, Deborah Polaski, Chicago Symphony Orchestra, Daniel Barenboim)",
        "Es reiten die Toten so schnell"                            : "Es reiten die Toten so schnell (Or: The Vampyre Sucking At His Own Vein)",
        "Escape From New York - O.S.T"                              : "Escape From New York - Original Motion Picture Soundtrack",
        "From The Flame Into The Fire (Deluxe Edition) (CD1)"       : "From The Flame Into The Fire (Deluxe Edition) (CD1: From The Flame Into The Fire)",
        "From The Flame Into The Fire (Deluxe Edition) (CD2)"       : "From The Flame Into The Fire (Deluxe Edition) (CD2: From The Rain Into The Flood)",
        "German Mystic Sound Sampler Vol. II"                       : "German Mystic Sound Sampler II",
        "Götterdämmerung (Pierre Boulez) (CD1)"                     : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD1)",
        "Götterdämmerung (Pierre Boulez) (CD2)"                 : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD2)",
        "Götterdämmerung (Pierre Boulez) (CD3)"                 : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD3)",
        "Götterdämmerung (Pierre Boulez) (CD4)"                 : "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD4)",
        "Gymnastic Label Compilation 1991-1995"                 : "Gymnastic Label Compilation",
        "Highlander II - The Quickening - O.S.T"                : "Highlander II - The Quickening - Music From And Inspired By The Film",
        "Ich Töte Mich Jedesmal Aufs Neue"                      : "Ich Töte Mich Jedesmal Aufs Neue, Doch Ich Bin Unsterblich, Und Ich Erstehe Wieder Auf ... - In Einer Vision Des Untergangs",
        "In Case You Didn't Feel Like Showing Up (Original Album Series)"   : "In Case You Didn't Feel Like Showing Up (Live) (Original Album Series)",
        "In Flimmernder Nacht"                       : "In Flimmernder Nacht ...",
        "Join The Dots - B-Sides & Rarities (CD1)"  : "Join The Dots - B-Sides & Rarities (CD1: 1978>1987)",
        "Join The Dots - B-Sides & Rarities (CD2)"  : "Join The Dots - B-Sides & Rarities (CD2: 1987>1992)",
        "Join The Dots - B-Sides & Rarities (CD3)"  : "Join The Dots - B-Sides & Rarities (CD3: 1992>1996)",
        "Join The Dots - B-Sides & Rarities (CD4)"  : "Join The Dots - B-Sides & Rarities (CD4: 1996>2001)",
        "La Chambre D'Echo"                         : "La Chambre D'Echo - Where The Dead Birds Sing",
        "Laugh - I Nearly Bought One!"              : "Laugh? I Nearly Bought One!",
        "Left Of The Dial (CD1)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD1)",
        "Left Of The Dial (CD2)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD2)",
        "Left Of The Dial (CD3)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD3)",
        "Left Of The Dial (CD4)"                    : "Left Of The Dial - Dispatches From The '80s Underground (CD4)",
        "Lexx - O.S.T"                              : "Lexx - Music From The Original Television Sci-Fi Movie Series",
        "Like A Corpse Standing In Desperation (CD1)"           : "Like A Corpse Standing In Desperation (CD1) - Original Demo Recordings",
        "Like A Corpse Standing In Desperation (CD2)"           : "Like A Corpse Standing In Desperation (CD2) - Voyager - The Jugglers Of Jusa", 
        "Like A Corpse Standing In Desperation (CD3)"           : "Like A Corpse Standing In Desperation (CD3) - Flowers In Formaldehyde",
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
        "Robin Hood - Prince Of Thieves - O.S.T"                : "Robin Hood - Prince Of Thieves - Original Motion Picture Soundtrack",
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
        "Todeswunsch"                                       : "Todeswunsch - Sous Le Soleil De Saturne",
        "Twilight Of The Gods Vol. 1 (CD1)"                 : "Twilight Of The Gods Vol. 1 - The Gothic-Metal-Collection (CD1)",
        "Twilight Of The Gods Vol. 1 (CD2)"                 : "Twilight Of The Gods Vol. 1 - The Gothic-Metal-Collection (CD2)",
        "Very 'Eavy ...Very 'Umble (Expanded De-Luxe Edition)"  : "...Very 'Eavy ...Very 'Umble (Expanded De-Luxe Edition)",
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
        "Wrack And Ruin (Limited Edition) (CD1)"            : "Wrack And Ruin (Limited Edition) (CD1: Wrack And Ruin)",
        "Wrack And Ruin (Limited Edition) (CD2)"            : "Wrack And Ruin (Limited Edition) (CD2: Maldiciones Para Un Mundo En Decadencia)",
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
    print(str, file=uni_stdout)

def parse_file(top_dir, full_path, md5_fh, csv_wh):
    global num_violations

    path_rel = pathlib.PurePath(full_path).relative_to(top_dir)

    if len(path_rel.parts) != 3:
        num_violations += 1
        my_print('violation: invalid file: {}'.format(full_path))
        return

    fname = path_rel.parts[2]
    if not is_valid_mp3_filename(fname):
        num_violations += 1
        print("violation: rule_3b: filenames must have format 'xx - Trackname.mp3'")
        print("file: {}".format(fname))
        return
    
    # tag is extracted anyway as it comes cheap, contrary to calculating
    # the MD5 hash which takes quite some time
    tag = extract_tag(full_path)
    if md5_fh:
        md5 = helpers.file_md5(full_path)
        md5_fh.write('{}  {}\n'.format(md5, path_rel))
    if csv_wh:
        csv_wh.writerow(tag)
    return tag

def report_mismatch(fname, item, f_item, t_item):
    global num_violations

    num_violations += 1
    my_print('Mismatch in {}, file: {} tag: {} (file: {})'.format(item, f_item, t_item, fname))

def report_substitution(reason, orig, sub):
    if enable_report_substitutions:
        sub = 'Replaced {}: {} with {}'.format(reason, orig, sub)
        substitutions_done.add(sub)

def is_mismatch(f_item, t_item, item):
    return True if f_item != t_item and report_mismatch_flags[item] else False

def match_artist(tag, item):
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

def match_album_artist(tag, item):
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
                    report_substitution('{}{}'.format(cat, i), t_item, f_item)
                    return True

    ### Multiple substitutions
    t_item_mod = t_item
    if cat in substitutions:
        subs = substitutions[cat]
        for i,v in enumerate(subs):
            for sub in subs[v]:
                t_item_mod = t_item_mod.replace(v, sub)
                if f_item == t_item_mod:
                    report_substitution('{}{}'.format(cat, i+10), t_item_mod, f_item)
                    return True

    if cat in ['AL', 'AR']:

        ### Remove trailing "..."
        m = re.search(r'^(.*)\.\.\.$', t_item_mod)
        if m and f_item == m.group(1):
            return True

        ### Remove leading "..." or "... "
        m = re.search(r'^\.\.\.\s{0,1}(.*)$', t_item_mod)
        if m and f_item == m.group(1):
            return True

        ### Remove trailing "."
        m = re.search(r'^(.*)\.$', t_item_mod)
        if m and f_item == m.group(1):
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
    for i,v in enumerate(ba):
        for c in chars:
            d = (ba[i]).to_bytes(1, 'big')
            if d == c:
                e = ba[i-1:i+2].decode('utf-8')
                return e

# check, whether MP3 filename convention is maintained 
def is_valid_mp3_filename(filename):
    m = re.match("^(\d\d) - (.*)\.mp3", filename)
    return True if m else False

# Extract info from file identified by path
def extract_tag(full_path):

    path = pathlib.PurePath(full_path)
    
    m = re.match("^(\d\d) - (.*)\.mp3", path.parts[-1])
    if m and len(m.groups()) == 2:
        ### Extract info from file and path
        tag = {}
        tag['f_artist'] = path.parts[-3]
        tag['f_album']  = path.parts[-2]
        tag['f_track'] = m.group(1)
        tag['f_title'] = m.group(2)

        ### Extract info from ID3 tag
        f = mutagen.File(full_path)
        if f:
            for k,v in tag_mapping.items():
                tag[v] = f[k].text[0] if k in f else ''
            
        return tag

def check_tag(tag):
    """
        Check file for errors or inconsistencies.

        Return value: Tag entry if no errors occured; None otherwise
    """

    global num_mp3
    global num_violations
    global file_longest
    global file_shortest


    full_path = '{}/{}/{} - {}.mp3'.format(tag['f_artist'], tag['f_album'], tag['f_track'], tag['f_title'])

    l = len(full_path)
    
    if file_shortest and l < len(file_shortest) or not file_shortest:
        file_shortest = full_path

    if file_longest and l > len(file_longest) or not file_longest:
        file_longest = full_path

    ### Scan for unwanted combining diacritical marks
    for k,v in tag.items():

        l = len(v)
        if stats_max[k] and l > len(stats_max[k]) or not stats_max[k]:
            stats_max[k] = v
        if stats_min[k] and l < len(stats_min[k]) or not stats_min[k]:
            stats_min[k] = v

        c = check_cdm(v)
        if c:
            my_print('CDM {} found: {} in {}'.format(c, k, full_path))

    ### Check tags

    unique_artists.add(tag['t_artist'])
    unique_albums.add(tag['t_album'])

    ### Track number must match exactly. No excuses...
    if is_mismatch(tag['f_track'], tag['t_track'], 'track'):
        report_mismatch(full_path, "Track number", tag['f_track'], tag['t_track'])

    ### Artist may not match exactly due to folder name restrictions
    if not match_artist(tag, 'artist'):
        report_mismatch(full_path, "Artist", tag['f_artist'], tag['t_artist'])

    ### Album artist may not match exactly due to compilations/missing fields
    if not match_album_artist(tag, 'album_artist'):
        report_mismatch(full_path, "Album artist", tag['f_artist'], tag['t_album_artist'])

    if not match_album(tag, 'album'):
        report_mismatch(full_path, "Album", tag['f_album'], tag['t_album'])

    if not match_title(tag, 'title'):
        report_mismatch(full_path, "Title", tag['f_title'], tag['t_title'])
    return tag

def parse_dir(top_dir, md5_fh, csv_wh):
    num_files = 0
    num_violations = 0
    num_mp3 = 0

    for dirpath, dirnames, filenames in os.walk(top_dir):
        dirnames.sort()
        filenames.sort()
        if (len(dirnames) == 0) and (len(filenames) == 0):
            num_violations += 1
            print("violation: rule_xx: empty folder detected: {}".format(dirpath))

        ### then, iterate over files
        for fname in filenames:
            num_files += 1
            tag = parse_file(top_dir, os.path.join(dirpath, fname), md5_fh, csv_wh)
            if tag:
                num_mp3 += 1

    return num_files, num_violations, num_mp3

def generate_list(top_dir, csv_file=None, md5_file=None):

    md5_fh = None
    csv_wh = None

    ### Open MD5 file
    if md5_file:
        md5_fh = open(md5_file, mode='w+', encoding='utf-8')

    ### Open CSV file
    if csv_file:
        csv_fh = open(csv_file, mode='w+', encoding='utf-8', errors='surrogateescape')
        csv_wh = csv.DictWriter(csv_fh, fieldnames=field_names, dialect='mp3_csv')
        csv_wh.writeheader()

    num_files, num_violations, num_mp3 = parse_dir(str(pathlib.PurePath(top_dir)), md5_fh, csv_wh)

    if md5_file:
        md5_fh.write('-------------------------------------------------------------\n')
        md5_fh.write("Top folder: {}\n".format(top_dir))
        md5_fh.write("{} file(s) checked\n".format(num_files))
        md5_fh.write("{} MP3 file(s) found\n".format(num_mp3))
        md5_fh.write("{} violation(s) found\n".format(num_violations))

    if md5_file:
        md5_fh.close()

    if csv_file:
        csv_fh.close()

    sys.exit(0)

def analyse_csv(csv_file):

    for f in field_names:
        stats_max[f] = None
        stats_min[f] = None

    ### Open and parse CSV file
    with open(csv_file, mode='r', encoding='utf-8', errors='surrogateescape') as f:
        reader = csv.DictReader(f, fieldnames=field_names, dialect='mp3_csv')
        for row in reader:
            if reader.line_num > 1:
                check_tag(row)

    ### Dump unique artists to file
    with open(unique_artists_file, "w", encoding='utf8') as f:
        for artist in sorted(unique_artists):
            f.write('{}\n'.format(artist))
    
    ### Dump unique albums to file
    with open(unique_albums_file, "w", encoding='utf8') as f:
        for album in sorted(unique_albums):
            f.write('{}\n'.format(album))

    if enable_report_substitutions:
        with open(substitutions_file, "w", encoding='utf8') as f:
            for line in sorted(substitutions_done):
                f.write('{}\n'.format(line))

    my_print('----------------------------------------------------')
    my_print('Path (max): {} {}'.format(len(file_longest), file_longest))
    my_print('Artist (max):')
    my_print('  Tag:  {:3d}   {}'.format(len(stats_max['t_artist']), stats_max['t_artist']))
    my_print('  File: {:3d}   {}'.format(len(stats_max['f_artist']), stats_max['f_artist']))
    my_print('Album (max):')
    my_print('  Tag:  {:3d}   {}'.format(len(stats_max['t_album']), stats_max['t_album']))
    my_print('  File: {:3d}   {}'.format(len(stats_max['f_album']), stats_max['f_album']))
    my_print('Title (max):')
    my_print('  Tag:  {:3d}   {}'.format(len(stats_max['t_title']), stats_max['t_title']))
    my_print('  File: {:3d}   {}'.format(len(stats_max['f_title']), stats_max['f_title']))

def print_usage_and_die():
    print("""Usage:
    -m <top_dir> <md5_file>             Check file hierarchy, naming rules etc. and dump MD5 hashes.
    -e <top_dir> <csv_file>             Extract MP3 tags starting from folder <top_dir> and dump tags to CSV file.
    -c <top_dir> <csv_file> <md5_file>  Combines options -m and -e.
    -a <csv_file>                  Analyse CSV file.
    """.format(sys.argv[0]))
    sys.exit(1)

def main():
    global uni_stdout

    ### Register dialect
    csv.register_dialect('mp3_csv', delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')

    ### Open another filehandle to stdout supporting UTF8 to prevent unicode issues with print()
    ### Note:   These problems may be only present when running the script locally and work flawless
    ###         over SSH.
    uni_stdout = open(1, 'w', encoding='utf-8', closefd=False)

    # Require at least one argument
    if len(sys.argv) < 2:
        print_usage_and_die()
    if sys.argv[1] == '-a' and len(sys.argv) == 3:
        analyse_csv(sys.argv[2])
    elif sys.argv[1] == '-e' and len(sys.argv) == 4:
        generate_list(sys.argv[2], csv_file=sys.argv[3])
    elif sys.argv[1] == '-m' and len(sys.argv) == 4:
        generate_list(sys.argv[2], md5_file=sys.argv[3])
    elif sys.argv[1] == '-c' and len(sys.argv) == 5:
        generate_list(sys.argv[2], csv_file=sys.argv[3], md5_file=sys.argv[4])
    else:
        print_usage_and_die()

    sys.exit(0)

if __name__ == '__main__':
    main()

