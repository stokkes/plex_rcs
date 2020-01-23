# Plex rclone cache scanner (plex_rcs)

A small python script that will monitor an rclone log file, waiting for notices of file cache expiration. Upon receiving a notice, a local Plex scan of that folder will be triggered and new media will appear in Plex almost instantly.

This is useful for people who run Plex Media Server on a different server than Sonarr/Radarr/etc.

## Requirements

1. Python 3+
2. Your rclone cache mount must include `--log-level INFO` **OR** if using VFS, it must be `--log-level DEBUG`
3. Your rclone cache mount must include `--syslog` **OR** * if using VFS, it must be `--log-file /path/to/file.log`

## Installation

1. Clone this repo: `git clone https://github.com/beyondmeat/plex_rcs.git`
2. Install the requirements: `pip3 install -r requirements.txt`

## Configuration



1. Copy the `config.yml.default` to `config.yml`
2. Edit `config.yml` to include your [X-Plex-Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/), set your `media_root` setting and any other settings. _See below for more information on the `media_root` setting_.

## Running plex_rcs

Using `screen` or using the included `plex_rcs.service` systemd service

### Using Windows:
Use nssm to create a service.

Example rclone mount for windows:

`mount gdrive:/ g: --user-agent="myuseragent/v1" --drive-skip-gdocs --timeout=30m --allow-other --dir-cache-time=72h --config "d:\rclone\rclone.conf" -o UserName=MYUSERNAME -o GroupName=Users --log-level=DEBUG --log-file=d:\plex_rcs\rclone.log`

### Using Linux

Example rclone mount for linux:

`mount gdrive:/ /mnt/media --user-agent="myuseragent/v1" --drive-skip-gdocs --timeout=30m --allow-other --dir-cache-time=72h --log-level=DEBUG --log-file=/path/to/log`


#### Using systemd

1. Edit the included `plex_rcs.service` file and change the path to where the `plex_rcs.py` file is located
2. Copy the systemd file to `/etc/systemd/service`: `sudo cp plex_rcs.service /etc/systemd/service`
3. Reload systemd: `sudo systemctl daemon-reload`
4. Enable the service [auto-starts on boot]: `sudo systemctl enable plex_rcs`
5. Start the service: `sudo systemctl start plex_rcs`

#### Using `screen`

Execute the program using screen:

`/usr/bin/screen -dmS plexrcs /path/to/plex_rcs/plex_rcs.py`

To view the console: `screen -r plexrcs`

## More info on `media_root` configuration setting

This setting may be tricky to figure out at the first glance, but it is critical to get `plex_rcs` working properly. 

The value of this setting is the folder **inside your docker container** (if using docker) that contains all your media. Typically, this would be in `/media` or `/data/media` or `/data`. If not using docker, this will likely be the path to your rclone mount, i.e.: `/mnt/media` or `g:\`

At this time there is 1 requirement:

The root of your rclone remote (i.e.: `gdrive:`) **must** contain all your media in sub-folders, so that the remote and the folder that is mounted inside your docker container/on your system both contain the same sub-folders.

**How to test:**

1. `rclone lsd gdrive:` and
2. `docker exec -ti plex ls /media` (where `/media` is where your media is located inside your docker container)
3. If not using docker, `ls /path/to/rclone/cache/mount`

If the result of these two folders yield the same sub-folders, then `plex_rcs` will work correctly.

**What won't work**

1. `rclone lsd cache:` shows many different folders, not just media sub-folders
2. You've mounted the `cache:` remote to `/mnt/media` using something like `rclone mount gdrive:Media /mnt/media`
2. `docker exec -ti plex ls /media` shows only your media sub-folders

## Testing

You can test `plex_rcs` if you use the built in /var/log/syslog monitoring by executing the following command (replace `tvshows` and the series/episode by your values):

### vfs mount
You must use a --log-file
Paste this at the end of the log file: (replace with valid path)
`2020/01/22 22:08:19 DEBUG : media/tv/Good Trouble (2019)/Season 2: invalidating directory cache`
### cache mount
`logger "Apr 21 07:20:51 plex rclone[21009]: tvshows/Survivor/Season 20/Survivor - S20E01 - Episode.mkv: received cache expiry notification"`

If you're monitoring the `plex_rcs` console, you should see activity:

```
Starting to monitor /var/log/syslog with pattern for rclone                                                             
Match found: tvshows/Survivor/Season 20/Survivor - S20E01 - Episode.mkv
Processing section 1, folder: /media/tvshows/Survivor/Season 20
GUI: Scanning Survivor/Season 20
```
