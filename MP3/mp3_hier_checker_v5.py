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
 

import sys
import re
import os.path
import shlex
import subprocess
import pathlib
import mutagen
import csv

num_files = 0
num_mp3 = 0
num_violations = 0

field_names = [
	'f_artist',			# artist (from filename)
	'f_album',			# album (from filename)
	'f_title',			# title (from filename)
	'f_track',			# track number (from filename)
	't_artist',			# artist (from tag, TPE1)
	't_album_artist',	# album artist (from tag, TPE2)
	't_album', 			# album (from tag, TALB)
	't_title',			# title (from tag, TIT2)
	't_track',			# track number (from tag, TRCK)
]

unique_artists = set()
unique_albums = set()

all_tags = list()

### Enable/disable debugging (True/False)
debug = False

report_mismatch_flags = {
	'artist'		: True,
	'album_artist'	: True,
	'album'			: True,
	'track'			: True,		# Don't change this entry!
	'title'			: False
}

tag_mapping = {
	'TRCK'	: 't_track',
	'TALB'	: 't_album',
	'TPE1'	: 't_artist',
	'TPE2'	: 't_album_artist',
	'TIT2'	: 't_title'
}

substitutions = {
	'artist' : {
		"à;Grumh"						: "à;Grumh...",
		"A7IE"							: ":A7IE:",
		"Adult"							: "Adult.",
		"All My Faith Lost"				: "All My Faith Lost...",
		"An Idea"						: "An:Idea",
		"Ascetic"						: "Ascetic:",
		"Bahntier"						: ":Bahntier//",
		"B. Says"						: "B. Says...",
		"B.E.F"							: "B.E.F.",
		"Boyd Rice & FriendsNON"		: "Boyd Rice & Friends/NON",
		"C.A.P"							: "C.A.P.",
		"C.O.C"							: "C.O.C.",
		"Carlos Peron - Peter Ehrlich"	: "Carlos Peron/Peter Ehrlich",
		"Charles Lindbergh N.E.V"		: "Charles Lindbergh N.E.V.",
		"Chameleons U.K"				: "Chameleons U.K.",
		"Concrete-Rage"					: "Concrete/Rage",
		"Crisk"							: "Crisk.",
		"De-Vision"						: "De/Vision",
		"D.I.D"							: "D.I.D.",
		"D.N.S"							: "D.N.S.",
		"Dinosaur Jr"					: "Dinosaur Jr.",
		"Ditto - Destroyer"				: "Ditto ≠ Destroyer",
		"Dope Stars Inc"				: "Dope Stars Inc.",
		"E.C.M"							: "E.C.M.",
		"E.R.R.A"						: "E.R.R.A.",
		"F-A-V"							: "F/A/V",
		"Fïx8-Sëd8"						: "Fïx8:Sëd8",
		"G.L.O.D"						: "G.L.O.D.",
		"Gary Numan - Tubeway Army"			: "Gary Numan/Tubeway Army",
		"Hell Sector"						: "Hell:Sector",
		"Golgatha"							: ":Golgatha:",
		"Golgatha And Dawn & Dusk Entwined"	: ":Golgatha: And Dawn & Dusk Entwined",
		"Golgatha & Birthe Klementowski"	: ":Golgatha: & Birthe Klementowski",
		"Hate Dept"						: "Hate Dept.",
                "Herbst9-Z'Ev"  : "Herbst9/Z'Ev",
                "Howden & Wakeford"         : "Howden/Wakeford",
		"I-Scintilla"					: "I:Scintilla",
		"In The Woods"					: "In The Woods...",
		"Keen K. Feat. Dorian E"				: "Keen K. Feat. Dorian E.",
		"L.E.A.K"						: "L.E.A.K.",
		"L.I.N"							: "L.I.N.",
		"L.S.G"							: "L.S.G.",
		"Land-Fire"						: "Land:Fire",
		"Lipps Inc"						: "Lipps Inc.",
		"Liquid G"						: "Liquid G.",
		"M.A.D"							: "M.A.D.",
		"Manic P"						: "Manic P.",
                "Mind-State"						: "Mind:State",
		"Mono Inc"						: "Mono Inc.",
                "N.D.M.A"                                               : "N.D.M.A.",
		"O.K"				: "O.K.",
		"O Quam Tristis"				: "O Quam Tristis...",
		"Of The Wand & The Moon"		: ":Of The Wand & The Moon:",
                "Osiris T" : "Osiris T.",
		"P1-E"										: "P1/E",
		"Patenbrigade Wolff"						: "Patenbrigade: Wolff",
		"Patenbrigade Wolff Feat. André Hartung"	: "Patenbrigade: Wolff Feat. André Hartung",
		"PP"							: "PP?",
		"Pretentious, Moi"				: "Pretentious, Moi?",
                "Project Komakino"              : "Project: Komakino",
		"ProTech"						: "Pro>Tech",
		"Public Image Ltd"				: "Public Image Ltd.",
		"Punch Inc"						: "Punch Inc.",
		"R.E.M"							: "R.E.M.",
		"Re-Legion"							: "Re:/Legion",
		"Re-Work"							: "Re/Work",
		"REC"								: "REC.",
		"Rozz Williams - Daucus Karota"		: "Rozz Williams/Daucus Karota",
		"[SITD]"							: "[:SITD:]",
		"S.V.D"								: "S.V.D.",
		"Sabotage Qu'est-ce Que C'est"					: "Sabotage Qu'est-ce Que C'est?",
		"Six Comm - Freya Aswynn"			: "Six Comm / Freya Aswynn",
		"Sixth Comm - Mother Destruction"	: "Sixth Comm / Mother Destruction",
		"Soon"						: "[Soon]",
		"S.K.E.T"					: "S.K.E.T.",
		"Shades Of Hell"			: "Shades:Of:Hell",
                "Spasmodique"   : ":Spasmodique:",
		"Star Inc"					: "Star Inc.",
		"Still Patient"				: "Still Patient?",
		"System-Eyes"				: r"System\\Eyes",
		"Temps Perdu"				: "Temps Perdu?",
		"The Dead Sexy Inc"				: "The Dead Sexy Inc.",
		"The Malice Inc"				: "The Malice Inc.",
		"The Sin-Decay"				: "The Sin:Decay",
		"Test Dept. - Brith Gof"	: "Test Dept. / Brith Gof",
		"T.A.C"						: "T.A.C.",
		"T.C"						: "T.C.",
		"T.C.H"						: "T.C.H.",
		"T.G.V.T"					: "T.G.V.T.",
		"T.H.D"						: "T.H.D.",
		"T.H.E"						: "T.H.E.",
		"T.O.Y"						: "T.O.Y.",
		"U.D.O"						: "U.D.O.",
		"Undergod"					: "Undergod.",
		"V.28"						: "V:28",
		"V.S.B"						: "V.S.B.",
		"W.A.S.P"					: "W.A.S.P.",
		"W.O.M.P"					: "W.O.M.P.",
		"Welle Erdball"				: "Welle: Erdball",
		"Witt - Heppner"			: "Witt / Heppner",
		"Wumpscut"					: ":Wumpscut:",
		"X-Dream Feat. Planet B.E.N"	: "X-Dream Feat. Planet B.E.N.",
		"Zoo"						: "//Zoo",
		"Zos Kia - Coil"			: "Zos Kia/Coil"
	},
	'album' : {
		"Like Clockwork"	: "...Like Clockwork",
		"2001 - A S.P.O.C.K Odyssey"	: "2001: A S.P.O.C.K Odyssey",
		"2003 A.D"	: "2003 A.D.",
		"4-13 Dream"	: "4:13 Dream",
		"Abattoir Blues - The Lyre Of Orpheus (CD1 - Abattoir Blues)"	: "Abattoir Blues / The Lyre Of Orpheus (CD1: Abattoir Blues)",
		"Abattoir Blues - The Lyre Of Orpheus (CD2 - The Lyre Of Orpheus)": "Abattoir Blues / The Lyre Of Orpheus (CD2: The Lyre Of Orpheus)",
		"Acoustic - La Ferrière-Harang - Bérigny, Normandie, France, 2011-2013"	: "Acoustic - La Ferrière-Harang/Bérigny, Normandie, France, 2011-2013",
		"A Guide To The Legendary Pink Dots - Vol. 1"	: "A Guide To The Legendary Pink Dots - Vol. 1 The Best Ballads",
		"A Question Of Time (CD1 - A Question Of Time)"	: "A Question Of Time (CD1: A Question Of Time)",
		"A Question Of Time (CD2 - Philharmonic Diseases)"	: "A Question Of Time (CD2: Philharmonic Diseases)",
		"All E.T.s Aren't Nice"	: "All E.T:s Aren't Nice",
		"An Entire Wardrobe Of Doubt And Uncertainty (CD1 - Album)"			: "An Entire Wardrobe Of Doubt And Uncertainty (CD1: Album)",
		"An Entire Wardrobe Of Doubt And Uncertainty (CD2 - Commentary)"	: "An Entire Wardrobe Of Doubt And Uncertainty (CD2: Patented Deadfly Ensemble Double Album Commentary)",
		"Aus Der Welt (The Collective Works 2000 - 2003)"	: "Aus Der Welt / Seduction Of Madness / Death, Dumb And Blind (The Collective Works 2000 - 2003)",
		"Barren Land (Limited Edition) (CD1 - Album)"	: "Barren Land (Limited Edition) (CD1: Album)",
		"Barren Land (Limited Edition) (CD2 - In The Midst Of Life, We Are In Death)"	: "Barren Land (Limited Edition) (CD2: In The Midst Of Life, We Are In Death)",
		"Bellum, Sacrum Bellum"	: "Bellum, Sacrum Bellum!?",
		"Bergwerk 2010 - DJ Francois Vs. Kartagon - The Remix Collection"	: "Bergwerk 2010 - DJ Francois Vs Kartagon - The Remix Collection",
		"Best Of (CD3) (Bonus CD - Live At Wacken 2015)"	: "Best Of (CD3) (Bonus CD: Live At Wacken 2015)",
		"Best Ov - Time's Up"	: "Best Ov: Time's Up",
		"Best Of Wagner - Walkürenritt - Ride Of The Valkyries"	: "Best Of Wagner - Walkürenritt/Ride Of The Valkyries",
		"Between The Eyes Vol. #1" : "Between The Eyes Vol. #1 (Singles/Rare B-Sides 1996-2000)",
		"Between The Eyes Vol. #2" : "Between The Eyes Vol. #2 (1994)",
		"Between The Eyes Vol. #3" : "Between The Eyes Vol. #3 (1994-1995)",
		"Between The Eyes Vol. #4" : "Between The Eyes Vol. #4 (1994-1995)",
		"Blade Runner Trilogy (CD2) - BR Prev. Unrel. & Bonus Material"		: "Blade Runner Trilogy (CD2) - Blade Runner Previously Unreleased & Bonus Material",
		"Cantar A La Morte - Fabula Triste"	: "Cantar A La Morte: Fabula Triste",
		"Celebrant 2004-05 - Der Mittelalterliche Klangkörper Zum WGT"	: "Celebrant 2004/05 - Der Mittelalterliche Klangkörper Zum Wave-Gotik-Treffen",
		"Chakra Red!"	: "¡Chakra : Red!",
		"Children Of The Corn (PE)"	: "Children Of The Corn (Premiere Edition)",
		"Cold Hands Seduction Vol. 36 (2004-04) (CD2)"	: "Cold Hands Seduction Vol. 36 (2004-04) (CD2) (Mittelaltermusik-Special Vol. II)", 
		"Cold Hands Seduction Vol. 46 (2005-03) (CD2)"	: "Cold Hands Seduction Vol. 46 (2005-03) (CD2) (Mittelalter-Special Vol. 3)",
		"Cold Hands Seduction Vol. 31 (2003-10) - CD1"	: "Cold Hands Seduction Vol. 31-1",
		"Cold Hands Seduction Vol. 31 (2003-10) - CD2"	: "Cold Hands Seduction Vol. 31-2",
		"Come With Me"	: "Come With Me...",
		"Construct Destruct"	: "Construct >< Destruct",
		"Crocodile Dundee - Original Motion Picture Score"	: "\"Crocodile\" Dundee - Original Motion Picture Score",
		"Dark Awakening Vol. 2 (CD1 - Electro)"	: "Dark Awakening Vol. 2 (CD1: Electro)",
		"Dark Awakening Vol. 2 (CD2 - Gothic)"	: "Dark Awakening Vol. 2 (CD2: Gothic)",
		"Darkness Calls"	: "Darkness Calls...",
		"Der Ring Des Nibelungen (Excerpts)"	:" Der Ring Des Nibelungen (Excerpts/Extraits/Auszüge, Deborah Polaski, Chicago Symphony Orchestra, Daniel Barenboim)",
		"Die Aesthetik Der Herrschaftsfreiheit (CD1 - Aufbruch)"	: "Die Aesthetik Der Herrschaftsfreiheit (CD1: Aufbruch Oder A Cross Of Wheat)",
		"Die Aesthetik Der Herrschaftsfreiheit (CD2 - Aufruhr)"		: "Die Aesthetik Der Herrschaftsfreiheit (CD2: Aufruhr Oder A Cross Of Fire)",
		"Die Aesthetik Der Herrschaftsfreiheit (CD3 - Aufgabe)"		: "Die Aesthetik Der Herrschaftsfreiheit (CD3: Aufgabe Oder A Cross Of Flowers)",
		"Die Flut (CD1)"											: "Die Flut - Die Benefiz Compilation Der Darkwave- Und Elektroszene (CD1)",
		"Die Flut (CD2)"											: "Die Flut - Die Benefiz Compilation Der Darkwave- Und Elektroszene (CD2)",
		"Die Singles 1993-2010 (CD01) - Nyntändo-Schock"			: "Die Singles 1993-2010 (CD01): Nyntändo-Schock",
		"Die Singles 1993-2010 (CD02) - W.O.L.F"					: "Die Singles 1993-2010 (CD02): W.O.L.F.",
		"Die Singles 1993-2010 (CD03) - Telephon W-38"				: "Die Singles 1993-2010 (CD03): Telephon W-38",
		"Die Singles 1993-2010 (CD04) - Deine Augen - Arbeit Adelt" : "Die Singles 1993-2010 (CD04): Deine Augen/Arbeit Adelt",
		"Die Singles 1993-2010 (CD05) - Starfighter F-104G"			: "Die Singles 1993-2010 (CD05): Starfighter F-104G",
		"Die Singles 1993-2010 (CD06) - VW Käfer & 1000 Tage"		: "Die Singles 1993-2010 (CD06): VW Käfer & 1000 Tage",
		"Die Singles 1993-2010 (CD07) - Super 8"					: "Die Singles 1993-2010 (CD07): Super 8",
		"Die Singles 1993-2010 (CD08) - Nur Tote Frauen Sind Schön" : "Die Singles 1993-2010 (CD08): Nur Tote Frauen Sind Schön",
		"Die Singles 1993-2010 (CD09) - Horizonterweiterungen"		: "Die Singles 1993-2010 (CD09): Horizonterweiterungen",
		"Die Singles 1993-2010 (CD10) - Ich Bin Aus Plastik"		: "Die Singles 1993-2010 (CD10): Ich Bin Aus Plastik",
		"Do Angels Never Cry, And Heaven"							: "Do Angels Never Cry, And Heaven Never Fall?",
		"Door To Insomnia"											: "Door To Insomnia...",
		"Emptiness Emptiness Emptiness"								: ":Emptiness:Emptiness:Emptiness:",
		"Emptiness Emptiness Emptiness (Remastered)"				: ":Emptiness:Emptiness:Emptiness: (Remastered)",
		"Eon Eon"	: "Eon:Eon",
		"Es reiten die Toten so schnell"	: "Es reiten die Toten so schnell (Or: The Vampyre Sucking At His Own Vein)",
		"Everything You Knew Was Wrong... (CD1 - Velvet Illusions)"	: "Everything You Knew Was Wrong... (CD1: Velvet Illusions)",
		"Everything You Knew Was Wrong... (CD2 - Velvet Suggestions)"	: "Everything You Knew Was Wrong... (CD2: Velvet Suggestions)",
		"German Mystic Sound Sampler Vol. II"		: "German Mystic Sound Sampler II",
		"Ghosts I-IV (CD1 - Ghosts I-II)"	: "Ghosts I-IV (CD1: Ghosts I-II)",
		"Ghosts I-IV (CD2 - Ghosts III-IV)"	: "Ghosts I-IV (CD2: Ghosts III-IV)",
		"Gothic Rock 2 (CD1 - Out Of The 80's...)"	: "Gothic Rock 2 (CD1: Out Of The 80's...)",
		"Gothic Rock 2 (CD2 - ...Into The 90's)"	: "Gothic Rock 2 (CD2: ...Into The 90's)",
		"Götterdämmerung (Pierre Boulez) (CD1)"	: "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD1)",
		"Götterdämmerung (Pierre Boulez) (CD2)"	: "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD2)",
		"Götterdämmerung (Pierre Boulez) (CD3)"	: "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD3)",
		"Götterdämmerung (Pierre Boulez) (CD4)"	: "Götterdämmerung (Bayreuther Festspiele, Pierre Boulez) (CD4)",
		"Gymnastic Label Compilation 1991-1995"	: "Gymnastic Label Compilation",
		"Have You Seen This Ghost"	: "Have You Seen This Ghost?",
		"Have You Seen This Ghost (Limited Edition)"	: "Have You Seen This Ghost? (Limited Edition)",
		"Have You Seen This Ghost (PE)"					: "Have You Seen This Ghost? (Premiere Edition)",
		"Highlander II - The Quickening - O.S.T"	: "Highlander II - The Quickening - Music From And Inspired By The Film",
		"Hotel Suicide (CD1 - Hotel Suicide)"	: "Hotel Suicide (CD1: Hotel Suicide)",
		"Hotel Suicide (CD2 - Room 13)"			: "Hotel Suicide (CD2: Room 13)",
		"How To Measure A Planet (CD1)" : "How To Measure A Planet? (CD1)",
		"How To Measure A Planet (CD2)" : "How To Measure A Planet? (CD2)",
		"Ich Töte Mich Jedesmal Aufs Neue"	: "Ich Töte Mich Jedesmal Aufs Neue, Doch Ich Bin Unsterblich, Und Ich Erstehe Wieder Auf ... - In Einer Vision Des Untergangs",
		"If I Die, I Die"	: "...If I Die, I Die",
		"In Case You Didn't Feel Like Showing Up (Original Album Series)"	: "In Case You Didn't Feel Like Showing Up (Live) (Original Album Series)",
		"In Memoriam - 1991-2007 (CD1 - The Grail)"	: "In Memoriam - 1991-2007 (CD1: The Grail)",
		"In Memoriam - 1991-2007 (CD2 - Rarities)"	: "In Memoriam - 1991-2007 (CD2: Rarities)",
		"Is Anybody There"	: "Is Anybody There?",
		"John Barleycorn Reborn - Rebirth (CD1)"	: "John Barleycorn Reborn : Rebirth (CD1)",
		"John Barleycorn Reborn - Rebirth (CD2)"	: "John Barleycorn Reborn : Rebirth (CD2)",
		"Join The Dots - B-Sides & Rarities (CD1)"	: "Join The Dots - B-Sides & Rarities (CD1: 1978>1987)",
		"Join The Dots - B-Sides & Rarities (CD2)"	: "Join The Dots - B-Sides & Rarities (CD2: 1987>1992)",
		"Join The Dots - B-Sides & Rarities (CD3)"	: "Join The Dots - B-Sides & Rarities (CD3: 1992>1996)",
		"Join The Dots - B-Sides & Rarities (CD4)"	: "Join The Dots - B-Sides & Rarities (CD4: 1996>2001)",
		"Künstler zum 14. Wave-Gotik-Treffen"	: "Künstler zum 14. WGT",
		"La Chambre D'Echo"	: "La Chambre D'Echo - Where The Dead Birds Sing",
		"Left Of The Dial (CD1)"	: "Left Of The Dial - Dispatches From The '80s Underground (CD1)",
		"Left Of The Dial (CD2)"	: "Left Of The Dial - Dispatches From The '80s Underground (CD2)",
		"Left Of The Dial (CD3)"	: "Left Of The Dial - Dispatches From The '80s Underground (CD3)",
		"Left Of The Dial (CD4)"	: "Left Of The Dial - Dispatches From The '80s Underground (CD4)",
		"Lexx - O.S.T"	: "Lexx - Music From The Original Television Sci-Fi Movie Series",
		"Like A Corpse Standing In Desperation (CD1)"	: "Like A Corpse Standing In Desperation (CD1) - Original Demo Recordings",
		"Like A Corpse Standing In Desperation (CD2)"	: "Like A Corpse Standing In Desperation (CD2) - Voyager - The Jugglers Of Jusa", 
		"Like A Corpse Standing In Desperation (CD3)"	: "Like A Corpse Standing In Desperation (CD3) - Flowers In Formaldehyde",
		"L.R.K"											: "L.R.K.",
		"Made In Germany (CD1 - 1995-2011)"	: "Made In Germany (CD1: 1995-2011)",
		"Made In Germany (CD2 - Remixes)"	: "Made In Germany (CD2: Remixes)",
		"Mellon Collie And The Infinite Sadness (CD1)"	: "Mellon Collie And The Infinite Sadness - Dawn To Dusk",
		"Mellon Collie And The Infinite Sadness (CD2)"	: "Mellon Collie And The Infinite Sadness - Twilight To Starlight",
		"Myth I - A Last Dance For The Things We Love"	: "Myth I: A Last Dance For The Things We Love",
		"Ogham Inside The Night (CD1 - Ogham Inside The Night)"	: "Ogham Inside The Night (CD1: Ogham Inside The Night)",
		"Ogham Inside The Night (CD2 - Sex And Wildflowers)"	: "Ogham Inside The Night (CD2: Sex And Wildflowers)",
		"Once Upon A Time - The Singles"				: "Once Upon A Time/The Singles",
		"On The Altar - In The Heart (CD1 - On The Altar)"	: "On The Altar - In The Heart (CD1: On The Altar)",
		"On The Altar - In The Heart (CD2 - In The Heart)"	: "On The Altar - In The Heart (CD2: In The Heart)",
		"Paradise"											: "Paradise... ?",
		"Phenomena (CD1 - Euphoria)"					: "Phenomena (CD1: Euphoria)",
		"Playlist - The Very Best Of Survivor"			: "Playlist: The Very Best Of Survivor",
		"Priest-Aura"	: "Priest=Aura",
		"Primitive Attentions"	: "Primitive Attentions...",
		"REC"	: "REC.",
		"Riding The Crest Of The Frozen Wave"	: "Riding The Crest Of The Frozen Wave - A Tribute To The Frozen Autumn",
		"Satan, Bugs Bunny, And Me"	: "Satan, Bugs Bunny, And Me...",
		"Sin Pecado (Original Album Collection)"	: "Sin / Pecado (Original Album Collection)",
		"To Bestial Gods"	: "To Bestial Gods...",
		"That First Season (Winter-Light) (CD1 - Heavy Snow)"	: "...That First Season (Winter-Light) (CD1: Heavy Snow)",
		"The Art Of Killing Silence (CD1 - Métodos Del Caos)"	: "The Art Of Killing Silence (CD1: Métodos Del Caos)",
		"The Art Of Killing Silence (CD2 - Noise Diary Plus Bonus)"	: "The Art Of Killing Silence (CD2: Noise Diary Plus Bonus)",
		"The Dark Box (CD1)"	: "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD1)",
		"The Dark Box (CD2)"	: "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD2)",
		"The Dark Box (CD3)"	: "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD3)",
		"The Dark Box (CD4)"	: "The Dark Box - The Ultimate Goth, Wave & Industrial Collection 1980-2011 (CD4)",
		"The Eye Of Time (CD1 - After Us)" : "The Eye Of Time (CD1: After Us)",
		"The Eye Of Time (CD2 - Jail - Lily On The Valley)" : "The Eye Of Time (CD2: Jail / Lily On The Valley)",
		"The Future Starts Here - The Essential Doors Hits"	: "The Future Starts Here: The Essential Doors Hits",
		"The Gothic Grotesque & Elektro Bizarre (Promo Edition)"	: "The Gothic Grotesque & Elektro Bizarre - Trisol Compilation 1 (Promo Edition)",
		"The Infinite (Promo)"		: "... The Infinite (Promo)",
		"The Most Spectacular Synthesizer Hits" : "The Most Spectacular Synthesizer Hits Of Vangelis, Jean-Michel Jarre & Jan Hammer Played By Star Inc.",
		"The Silhouette Scene E.P"		: "The Silhouette Scene E.P.",
		"The Triumph Of Light"	: "The Triumph Of Light... And Thy Thirteen Shadows Of Love",
		"Todeswunsch"	: "Todeswunsch - Sous Le Soleil De Saturne",
		"Twilight Of The Gods Vol. 1 (CD1)"		: "Twilight Of The Gods Vol. 1 - The Gothic-Metal-Collection (CD1)",
		"Twilight Of The Gods Vol. 1 (CD2)"		: "Twilight Of The Gods Vol. 1 - The Gothic-Metal-Collection (CD2)",
		"Very 'Eavy ...Very 'Umble (Expanded De-Luxe Edition)"	: "...Very 'Eavy ...Very 'Umble (Expanded De-Luxe Edition)",
		"Wenches, Wytches And Vampyres - The Very Best Of Two Witches"	: "Wenches, Wytches And Vampyres - The Very Best Of Two Witches 1987-1999",
		"What Happened Behind The Door"	: "What Happened Behind The Door?",
		"What If"	: "What If...",
		"What Sweet Music They Make - The Best Of (CD1)"	: "Thee Vampire Guild - What Sweet Music They Make - The Best Of (CD1)",
		"What Sweet Music They Make - The Best Of (CD2)"	: "Thee Vampire Guild - What Sweet Music They Make - The Best Of (CD2)",
		"Who Watches Over Me"	: "Who Watches Over Me?",
		"Works & Passion 1955 - 2000 (CD1)"	: "Works & Passion 1955 - 2000 (CD1: The Feetwarmers - The Quartet - Paul Nero - Motherhood)",
		"Works & Passion 1955 - 2000 (CD3)"		: "Works & Passion 1955 - 2000 (CD3: Passport 1971 - 1980)",
		"Works & Passion 1955 - 2000 (CD4)"		: "Works & Passion 1955 - 2000 (CD4: Passport 1980 - 2000)",
		"Zillo CD 12-05-01-06"	: "Zillo CD 12/05-01/06 (Spoken Word - Dunkle Lesungen)",
		"ZilloScope New Signs & Sounds 03-04"				: "ZilloScope 03/04",
		"ZilloScope New Signs & Sounds 8_9-02"	: "ZilloScope 8-9/02",
		"ZilloScope New Signs & Sounds 7-03"	: "ZilloScope 7/03",
		"Zillo Scope 7_8-98"	: "Zillo Scope 7/8-98",
		"ZilloScope New Signs & Sounds 12_03-01_04"		: "ZilloScope 12/03 1/04",
		"ZilloScope New Signs & Sounds 11-03"	: "ZilloScope 11/03",
		"ZilloScope New Signs & Sounds 8_9-03"	: "ZilloScope 8-9/03",
		"ZilloScope New Signs & Sounds 07-04"	: "ZilloScope 7/04",
		"ZilloScope New Signs & Sounds 10-03"	: "ZilloScope 10/03",
		"Zos Kia - Coil - Transparent"	: "Zos Kia/Coil - Transparent",
		"Zwischenfall - From The 80's To The 90's Vol. 2 (CD1)"	: "Zwischenfall Vol. 2 (CD1)",
		"Zwischenfall - From The 80's To The 90's Vol. 2 (CD2)"	: "Zwischenfall Vol. 2 (CD2)",
	}
}

### files
unique_artists_file = "unique_artists.txt"
unique_albums_file = "unique_albums.txt"

### strip trailing newline and convert to UTF-8
def strip_shell(txt):
	return txt[:-1].decode('utf-8')

def file_md5(file):
	cmd = '/usr/bin/md5sum "{}"'.format(file)
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	txt = strip_shell(p.stdout.read())
	md5 = txt.split()[0]
	return md5

def my_print(str):
	"""
		Wraper to use alternate stdout handle capable of UTF-8 irregarding of environment.
	"""
	print(str, file=uni_stdout)

def parse_file(top_dir, full_path, md5_fh, csv_wh):
	global num_violations

	tag = {}

	path_rel = pathlib.PurePath(full_path).relative_to(top_dir)

	if len(path_rel.parts) != 3:
		num_violations += 1
		print('violation: invalid file: {}'.format(full_path))
		return

	fname = path_rel.parts[2]

	m = re.match("^(\d\d) - (.*)\.mp3", fname)
	if m and len(m.groups()) == 2:

		if md5_fh:
			md5 = file_md5(full_path)
			md5_fh.write('{}  {}\n'.format(md5, path_rel))

		if csv_wh:

			### Extract info from file and path
			tag['f_artist'] = path_rel.parts[0]
			tag['f_album']	= path_rel.parts[1]
			tag['f_track'] = m.group(1)
			tag['f_title'] = m.group(2)

			### Extract info from ID3 tag
			f = mutagen.File(full_path)
			if f:
				for k,v in tag_mapping.items():
					tag[v] = f[k].text[0] if k in f else ''

			if debug:
				print('-----------------------------')
				print(full_path)
				my_print(f.tags.pprint())
#			for k,v in tag.items():
#				my_print('{} : {}'.format(k, v))

			csv_wh.writerow(tag)

	else:
		num_violations += 1
		print("violation: rule_3b: filenames must have format 'xx - Trackname.mp3'")
		print("file: {}".format(fname))
	return tag

def report_mismatch(fname, item, f_item, t_item):
	global num_violations

	num_violations += 1
	print('Mismatch in {}, file: {} tag: {} (file: {})'.format(item, f_item, t_item, fname))


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

	if f_artist == t_artist:
		### Perfect match
		return True

	if f_artist == t_artist.replace('/', '-').replace(':', ''):
		### Standard replacement
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

	if not report_mismatch_flags['album_artist']:
		### Check disabled
		return True

	if t_artist == t_album_artist:
		### Perfect match
		return True

	if t_album_artist in ['Various Artists', '']:
		### Compilation
		return True

	### Still not matching -> error
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

	if f_album == t_album:
		### Perfect match
		return True

	if f_album == t_album.replace('/', '-').replace(':', ''):
		### Standard replacement
		return True

	### Check, whether there is a substitution available
	if f_album in substitutions['album']:
		if t_album == substitutions[item][f_album]:
			### Substitute matches
			return True

	### Still not matching -> error
	return False

def check_tag(tag):
	"""
		Check file for errors or inconsistencies.

		Return value: Tag entry if no errors occured; None otherwise
	"""

	global num_mp3
	global num_violations

	full_path = '{}/{}/{} - {}.mp3'.format(tag['f_artist'], tag['f_album'], tag['f_track'], tag['f_title'])

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

	return tag

def parse_dir(top_dir, md5_fh, csv_wh):
	global num_files
	global num_violations
	global num_mp3

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
				all_tags.append(tag)
				num_mp3 += 1

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

	parse_dir(str(pathlib.PurePath(top_dir)), md5_fh, csv_wh)

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

def print_usage_and_die():
	print("""Usage:
	-m <top_dir> <md5_file>             Check file hierarchy, naming rules etc. and dump MD5 hashes.
	-e <top_dir> <csv_file>        	    Extract MP3 tags starting from folder <top_dir> and dump tags to CSV file.
	-c <top_dir> <csv_file> <md5_file>	Combines options -m and -c.
	-a <csv_file>                  Analyse CSV file.
	""".format(sys.argv[0]))
	sys.exit(1)

def main():
	global uni_stdout

	### Register dialect
	csv.register_dialect('mp3_csv', delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')

	### Open another filehandle to stdout supporting UTF8 to prevent unicode issues with print()
	### Note:	These problems may be only present when running the script locally and work flawless
	###			over SSH.
	uni_stdout = open(1, 'w', encoding='utf-8', closefd=False)

	if len(sys.argv) == 3 and sys.argv[1] == '-a':
		analyse_csv(sys.argv[2])
	elif len(sys.argv) == 4 and sys.argv[1] == '-e':
		generate_list(sys.argv[2], csv_file=sys.argv[3])
	elif len(sys.argv) == 4 and sys.argv[1] == '-m':
		generate_list(sys.argv[2], md5_file=sys.argv[3])
	elif len(sys.argv) == 5 and sys.argv[1] == '-c':
		generate_list(sys.argv[2], csv_file=sys.argv[3], md5_file=sys.argv[4])
	else:
		print_usage_and_die()

	sys.exit(0)

main()

