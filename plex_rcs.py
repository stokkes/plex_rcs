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
import tailer


def config(file):
    global plex, cfg

    with open(file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile,Loader=yaml.FullLoader)['plex_rcs']

    try:
        plex = PlexServer(
            "http://{0}:{1}".format(cfg['host'], cfg['port']), cfg['token'])
        if args.test:
            print("Config OK. Successfully connected to Plex server on {0}:{1}".format(
                cfg['host'], cfg['port']))
    except:
        sys.exit("Failed to connect to plex server {0}:{1}.".format(
            cfg['host'], cfg['port']))
            
def build_sections():
    global paths

    # Build our library paths dictionary
    for section in plex.library.sections():
        for l in plex.library.section(section.title).locations:
            paths.update({l: section.key})


def scan(folder):

    # if cfg['media_root'].rstrip("\\").rstrip("/") in folder:
    #     directory = args.directory
    #     print("directory: '{0}'".format(
    #         directory))
    # else:
    directory = os.path.abspath("{0}/{1}".format(cfg['media_root'].rstrip("\\").rstrip("/"), folder))
    print("directory: '{0}'".format(
        directory))

    # Match the new file with a path in our library
    # and trigger a scan via a `docker exec` call
    found = False

    for p in paths:
        if p in directory:
            found = True
            section_id = paths[p]
            print("Processing section {0}, folder: {1}".format(
                section_id, directory))

            if cfg['docker']:
                try:
                    call(["/usr/bin/docker", "exec", "-it", cfg['container'], "bash", "-c",
                          "export LD_LIBRARY_PATH=/usr/lib/plexmediaserver/lib;/usr/lib/plexmediaserver/Plex\ Media\ Scanner" " --scan" " --refresh" " --section {0} --directory '{1}'".format(section_id, directory)])
                except:
                    print("Error executing docker command")
            else:
                os.environ['LD_LIBRARY_PATH'] = os.path.expandvars(cfg['env']['LD_LIBRARY_PATH'])
                os.environ['PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR'] = os.path.expandvars(cfg['env']['PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR'])
                try:
                    call(["{0}/Plex Media Scanner".format(os.path.expandvars(cfg['env']['LD_LIBRARY_PATH'])), "--scan",
                          "--refresh", "--section", section_id, "--directory", directory], env=os.environ)
                except:
                    print(
                        "Error executing {0}/Plex Media Scanner".format(os.path.expandvars(cfg['env']['LD_LIBRARY_PATH'])))

    if not found:
        print("Scanned directory '{0}' not found in Plex library".format(
            directory))


def tailf(logfile):
    print("Starting to monitor {0} with pattern for rclone {1}".format(
        logfile, cfg['backend']))

    # Validate which backend we're using
    if cfg['backend'] == 'cache':
        # Use cache backend
        for line in tailer.follow(open(logfile)):
            if re.match(r".*(mkv:|mp4:|mpeg4:|avi:) received cache expiry notification", line):
                f = re.sub(
                    r"^(.*rclone\[[0-9]+\]: )([^:]*)(:.*)$", r'\2', line)
                print("Detected new file: {0}".format(f))
                scan(os.path.dirname(f))

    elif cfg['backend'] == 'vfs':
        # Use vfs backend
        timePrev = ''
        for line in tailer.follow(open(logfile)):
            if re.match(r".*\:\sinvalidating directory cache", line):
                files = re.search(r"\:\s(.*)\:", line)
                f = files.group(1)
                timeCurr = re.sub(
                    r"^.*\s(\d+:\d+:\d+)\s.*\s:\s.*\:\sinvalidating directory cache", r'\1', line)

                if timeCurr != timePrev:
                    print("Detected directory cache expiration: {0}".format(f))
                    scan(f)
                    timePrev = timeCurr

def find_log():
    if args.logfile:
        lf = args.logfile
        if not os.path.isfile(lf):
            print("Log file '{0}' does not exist.".format(args.logfile))
            sys.exit(1)
    else:
        lf = cfg['log_file']
        if not os.path.isfile(lf):
            print("Log file {0} does not exist.".format(lf))
            sys.exit(1)

    return lf

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="plex_rcs_helper.py", description="Small helper script to update a Plex library section by scanning a specific directory.")
    parser.add_argument("-d", "--directory", dest="directory",
                        metavar="directory", help="Directory to scan")
    parser.add_argument("-l", "--logfile", dest="logfile", metavar="logfile",
                        help="Log file to monitor (default /var/log/syslog)")
    parser.add_argument("-c", "--config", dest="config",
                        metavar="config", help="config file")
    parser.add_argument("--test", action='store_true', help="Test config")
    args = parser.parse_args()

    # Initialize our paths dict
    paths = {}

    # Configuration file
    if args.config:
        cf = args.config
        if not os.path.isfile(cf):
            print("Configuration file '{0}' does not exist.".format(
                args.config))
            sys.exit(1)
    else:
        cf = "{0}/config.yml".format(
            os.path.dirname(os.path.realpath(__file__)))
        if not os.path.isfile(cf):
            print("Configuration file '{0}' does not exist.".format(
                os.path.dirname(os.path.realpath(__file__))))
            sys.exit(1)

    # Main
    if args.test:
        config(cf)
        find_log()
    elif args.directory:
        config(cf)
        find_log()
        build_sections()
        scan(args.directory)
    else:
        config(cf)
        lf = find_log()
        build_sections()
        tailf(lf)
