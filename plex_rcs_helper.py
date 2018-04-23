#!/usr/bin/env python3
#
# Helper script
# 
import os
import sys
import yaml
import argparse
from plexapi.myplex import PlexServer
from subprocess import call


def config():
	global plex, cfg

	with open("config.yml", 'r') as ymlfile:
		cfg = yaml.load(ymlfile)['plex_rcs']

	try:
		plex = PlexServer("http://%s:%s" % (cfg['host'], cfg['port']), cfg['token'])
		if args.test:
			print("Config OK. Successfully connected to Plex server on %s" % (cfg['host'], cfg['port']), cfg['token'])
	except:
		sys.exit("Failed to connect to plex server %s." % (cfg['host'], cfg['port']), cfg['token'])

def build_sections():
	global paths

	# Build our library paths dictionary
	for section in plex.library.sections():
		for l in plex.library.section(section.title).locations:
			paths.update({l:section.key})

def scan():
	
	if cfg['media_root'] in args.directory:
		directory = args.directory
	else:
		directory = "%s/%s" % (cfg['media_root'], args.directory)
	
	# Match the new file with a path in our library
	# and trigger a scan via a `docker exec` call
	for p in paths:
		if p in directory:
			section_id = paths[p]
			print("Processing section %s, folder: %s" % (section_id, directory))
			
			if cfg['docker']:
				try:
					call(["/usr/bin/docker", "exec", "-i", cfg['container'], "/usr/lib/plexmediaserver/Plex Media Scanner", "--scan", "--refresh", "--section", section_id, "--directory", directory])
				except:
					print("Error executing docker command")
			else:
				os.environ['LD_LIBRARY_PATH'] = cfg['env']['LD_LIBRARY_PATH']
				os.environ['PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR'] = cfg['env']['PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR']
				try:
					call(["%s/Plex Media Scanner" % cfg['env']['LD_LIBRARY_PATH'], "--scan", "--refresh", "--section", section_id, "--directory", directory], env=os.environ)
				except:
					print("Error executing %s/Plex Media Scanner" % cfg['env']['LD_LIBRARY_PATH'])

if __name__ == "__main__":

	parser = argparse.ArgumentParser(prog="plex_rcs_helper.py", description="Small helper script to update a Plex library section by scanning a specific directory.")
	parser.add_argument("-d", "--directory", dest="directory", metavar="directory", help="Directory to scan")
	parser.add_argument("--test", action='store_true', help="Test config")
	args = parser.parse_args()
	
	# Initialize our paths dict
	paths = {}

	if args.test:
		config()
	elif args.directory:		
		# Build config
		config()
		
		# Build sections
		build_sections()
		
		# Scan directory
		scan()		
