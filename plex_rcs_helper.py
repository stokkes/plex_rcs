#!/usr/bin/env python3
#
# Helper script
# 
import sys
import yaml
import argparse
from plexapi.myplex import PlexServer
from subprocess import call


def config():
	global plex, plex_url, plex_token, root_folder

	with open("config.yml", 'r') as ymlfile:
		cfg = yaml.load(ymlfile)


	plex_url = "http://%s:%s" % (cfg['plex_rcs']['host'], cfg['plex_rcs']['port'])
	plex_token = cfg['plex_rcs']['token']
	root_folder = cfg['plex_rcs']['docker_media_root']
	
	try:
		plex = PlexServer(plex_url, plex_token)
		if args.test:
			print("Config OK. Successfully connected to Plex server on %s" % plex_url)
	except:
		sys.exit("Failed to connect to plex server %s." % plex_url)	

def build_sections():
	global paths

	# Build our library paths dictionary
	for section in plex.library.sections():
		for l in plex.library.section(section.title).locations:
			paths.update({l:section.key})

def scan():
	global root_folder, directory
	
	if root_folder in args.directory:
		directory = args.directory
	else:
		directory = "%s/%s" % (root_folder, args.directory)
	
	# Match the new file with a path in our library
	# and trigger a scan via a `docker exec` call
	for p in paths:
		if p in directory:
			section_id = paths[p]
			print("Processing section %s, file: %s" % (section_id, directory))
			call(["/usr/bin/docker", "exec", "-i", "plex", "/usr/lib/plexmediaserver/Plex Media Scanner", "--scan", "--refresh", "--section", section_id, "--directory", directory])
		

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
