#!/usr/bin/python

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

import sys,re,os.path,dircache

no_files = 0;
no_mp3 = 0;
no_violations = 0;

def main():
	check_dir(sys.argv[1],1)
	print "check finished";
	print str(no_files) + " file(s) checked";
	print str(no_mp3) + " MP3 file(s) found";
	print str(no_violations) + " violation(s) found";
	sys.exit(0)

def check_dir(work_dir,level):
	global no_files;
	global no_mp3;
	global no_violations;
	for x in dircache.listdir(work_dir): # traverse all dirs and files in work_dir
		full_path=os.path.join(work_dir,x)
		if (os.path.isdir(full_path)):
			if (level==3):
				no_violations+=1;
				print "violation: rule_3a: no directories are allowed in level 3";
				print "dir: ", os.path.basename(full_path);
			if (level<3):
				check_dir(full_path,level+1) # recursive call
		elif (os.path.isfile(full_path)):
			no_files= no_files + 1;
			if (level==1):
				no_violations+=1;
				print "violation: rule_1a: no files are allowed in level 1";
				print "file: ", os.path.basename(full_path);
			elif (level==2):
				no_violations+=1;
				print "violation: rule_2a: no files are allowed in level 2";
				print "file: ", os.path.basename(full_path);
			elif (level==3):
				result =re.match("^\d\d - .*\.mp3", os.path.basename(full_path));
				if (not result):
					no_violations += 1;
					print "violation: rule_3b: filenames must have format 'xx - Trackname.mp3'";
					print "file: ", os.path.basename(full_path);
				elif (os.path.isfile(full_path)):
					no_mp3 += 1;
					os.system("md5sum \"" + full_path + "\"")

main()

