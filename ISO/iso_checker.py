#!/usr/bin/python3

# last modification: 2015-10-25

import sys,re,os.path, subprocess, shlex
import pathlib

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers

num_iso = 0
num_corrupt = 0
no_mp3 = 0
no_violations = 0

mount_point = "/dvd_mp"
scan_iso_content = False
create_checksums = False

### file extensions of files which will report as type 'data'
file_ext_whitelist = ['.mov', '.dcr', '.ins', '.pkg', '.ex_', '.bin', '.ins', '.dmg', '.lay', '.tlb', '.dxr', '.scc']

def _mount_iso(file, mount_point):
	cmd = '/bin/mount -r "{}" {}'.format(file, mount_point)
	args = shlex.split(cmd)
	res = subprocess.run(args, stdout=subprocess.PIPE)
	return res
	
	txt = res.stdout
	ec = res.returncode
	print('Returncode {}'.format(ec))
	return txt

def mount_iso(file, mount_point):

	res = _mount_iso(file, mount_point)
	if res.returncode == 1:
		# Already mounted, unmount and try again
		unmount_iso(mount_point)

		res = _mount_iso(file, mount_point)
		if res.returncode != 0:
			# Failed again
			print('Failed to mount {} on {}'.format(file, mount_point))

	return res.stdout

def unmount_iso(mount_point):
	cmd = '/bin/umount "{}"'.format(mount_point)
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	txt = p.stdout.read()
	return txt

def check_dvd(folder):
#	global num_corrupt
	corrupt_files = 0

	for x in os.listdir(folder): # traverse all dirs and files in mount_point
		full_path=os.path.join(folder,x)
		if (os.path.isdir(full_path)):
			### descend to folder (recursively)
			corrupt_files += check_dvd(full_path)
		elif (os.path.isfile(full_path)):
			### print size and MD5 of ISO
			size	= file_size(full_path)
			type	= file_type(full_path)
			if create_checksums:
				md5	= file_md5(full_path)
			else:
				md5	= ''

			if type == 'data':
				file_name, file_ext = os.path.splitext(full_path)
				if file_ext.lower() not in file_ext_whitelist:
					print('corrupt: {} {}'.format(file_name, file_ext))
					corrupt_files += 1

			print('{} {:>10}      {}     {}'.format(md5, size, full_path.replace(mount_point+'/', ''),type))
	return corrupt_files

def check_dir(work_dir):
	global num_corrupt
	global num_iso;
	corrupt = 0

	for x in os.listdir(work_dir): # traverse all dirs and files in work_dir
		full_path=os.path.join(work_dir,x)
		if (os.path.isdir(full_path)):
			### descend to folder (recursively)
			check_dir(full_path)
		if (os.path.isfile(full_path)):
				result =re.match("^.*\.iso", os.path.basename(full_path));
				if (result):
					### print size and MD5 of ISO
					num_iso = num_iso + 1;
	
					size	= file_size(full_path)
					if create_checksums:
						md5	= file_md5(full_path)
					else:
						md5	= ''

					print('{} {} {}'.format(md5, size, full_path))
					if scan_iso_content:
						mount_iso(full_path, mount_point)
						corrupt = check_dvd(mount_point)
						if corrupt > 0:
							print('corrupt ISO: {}'.format(full_path))
						num_corrupt += corrupt
						unmount_iso(mount_point)

def print_usage_and_quit():
	print("usage: iso_checker xxx folder")
	print("arguments:")
	print(" -f  Scan ISO content")
	print(" -m  Create MD5 checksums")
	sys.exit(0)

if __name__ == '__main__':
	argc = len(sys.argv)
	if argc == 1:
		print_usage_and_quit()

	for arg in sys.argv[1:]:
		if arg == '-f':
			scan_iso_content = True
		if arg == '-m':
			create_checksums = True
	
	if not os.path.exists(mount_point):
		print("Mount point {} does not exist".format(mount_point))
		sys.exit(0)

	### last arg is supposed to be the start folder
	start_dir = sys.argv[-1]
	if not os.path.isdir(start_dir):
		print("{} is not a valid folder".format(start_dir))
		print_usage_and_quit()

	check_dir(start_dir)
	print("number of ISOs scanned: {}".format(num_iso))
	print("number of corrupt files: {}".format(num_corrupt))
	sys.exit(0)


