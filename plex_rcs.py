#!/usr/bin/python3
#
# Helper script
#
import os
import sys
import re
import argparse
import yaml
import time
from datetime import datetime
from subprocess import call
from plexapi.myplex import PlexServer
from sh import tail

def config(file):
	global plex, cfg

	with open(file, 'r') as ymlfile:
		cfg = yaml.load(ymlfile)['plex_rcs']

	try:
		plex = PlexServer("http://{0}:{1}".format(cfg['host'], cfg['port']), cfg['token'])
		if args.test:
			print("Config OK. Successfully connected to Plex server on {0}:{1}".format(cfg['host'], cfg['port']))
	except:
		sys.exit("Failed to connect to plex server {0}:{1}.".format(cfg['host'], cfg['port']))

def build_sections():
	global paths

	# Build our library paths dictionary
	for section in plex.library.sections():
		for l in plex.library.section(section.title).locations:
			paths.update({l:section.key})

def scan(folder):

	if cfg['media_root'].rstrip("/") in folder:
		directory = args.directory
	else:
		directory = "{0}/{1}".format(cfg['media_root'].rstrip("/"), folder)

	# Match the new file with a path in our library
	# and trigger a scan via a `docker exec` call
	found = False

	for p in paths:
		if p in directory:
			found = True
			section_id = paths[p]
			print("Processing section {0}, folder: {1}".format(section_id, directory))

			if cfg['docker']:
				try:
					call(["/usr/bin/docker", "exec", "-i", cfg['container'], "/usr/lib/plexmediaserver/Plex Media Scanner", "--scan", "--refresh", "--section", section_id, "--directory", directory])
				except:
					print("Error executing docker command")
			else:
				os.environ['LD_LIBRARY_PATH'] = cfg['env']['LD_LIBRARY_PATH']
				os.environ['PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR'] = cfg['env']['PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR']
				try:
					call(["{0}/Plex Media Scanner".format(cfg['env']['LD_LIBRARY_PATH']), "--scan", "--refresh", "--section", section_id, "--directory", directory], env=os.environ)
				except:
					print("Error executing {0}/Plex Media Scanner".format(cfg['env']['LD_LIBRARY_PATH']))

	if not found:
		print("Scanned directory '{0}' not found in Plex library".format(args.directory))

def tailf(logfile):
	print("Starting to monitor {0} with pattern for rclone {1}".format(logfile, cfg['backend']))

	# Validate which backend we're using
	if cfg['backend'] == 'cache':
		# Use cache backend
		for line in tail("-Fn0", logfile, _iter=True):
			if re.match(r".*(mkv:|mp4:|mpeg4:|avi:) received cache expiry notification", line):
				f = re.sub(r"^(.*rclone\[[0-9]+\]: )([^:]*)(:.*)$",r'\2', line)
				print("Detected new file: {0}".format(f))
				scan(os.path.dirname(f))

	elif cfg['backend'] == 'vfs':
		# Use vfs backend
		timePrev = ''
		for line in tail("-Fn0", logfile, _iter=True):
			if re.match(r".*: forgetting directory cache", line):
				f = re.sub(r"^.*\s:\s(.*):\sforgetting directory cache",r'\1', line)
				timeCurr = re.sub(r"^.*\s([0-9]+:[0-9]+:[0-9]+)\s.*\s:\s.*:\sforgetting directory cache",r'\1', line)

				if timeCurr != timePrev:
					print("Detected directory cache expiration: {0}".format(f))
					scan(os.path.dirname(f))
					timePrev = timeCurr


if __name__ == "__main__":

	parser = argparse.ArgumentParser(prog="plex_rcs_helper.py", description="Small helper script to update a Plex library section by scanning a specific directory.")
	parser.add_argument("-d", "--directory", dest="directory", metavar="directory", help="Directory to scan")
	parser.add_argument("-l", "--logfile", dest="logfile", metavar="logfile", help="Log file to monitor (default /var/log/syslog)")
	parser.add_argument("-c", "--config", dest="config", metavar="config", help="config file")
	parser.add_argument("--test", action='store_true', help="Test config")
	args = parser.parse_args()

	# Initialize our paths dict
	paths = {}

	# Configuration file
	if args.config:
		cf = args.config
		if not os.path.isfile(cf):
			print("Configuration file '{0}' does not exist.".format(args.config))
			sys.exit(1)
	else:
		cf = "{0}/config.yml".format(os.path.dirname(os.path.realpath(__file__)))
		if not os.path.isfile(cf):
			print("Configuration file '{0}' does not exist.".format(os.path.dirname(os.path.realpath(__file__))))
			sys.exit(1)

	# Logfile
	if args.logfile:
		lf = args.logfile
		if not os.path.isfile(cf):
			print("Log file '{0}' does not exist.".format(args.logfile))
			sys.exit(1)
	else:
		lf = "/var/log/syslog"
		if not os.path.isfile(cf):
			print("Log file '/var/log/syslog' does not exist.".format(args.config))
			sys.exit(1)

	# Main
	if args.test:
		config(cf)
	elif args.directory:
		# Build config
		config(cf)

		# Build sections
		build_sections()

		# Scan directory
		scan(args.directory)
	else:
		# Build config
		config(cf)

		# Build sections
		build_sections()

		# Scan directory
		tailf(lf)
