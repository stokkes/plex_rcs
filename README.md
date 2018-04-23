# Plex rclone cache scanner (plex_rcs)

A small little program that will monitor an rclone log file (using `tail`) waiting for notices of file cache expiration. Upon receiving a notice, it will evoke its helper script `plex_rcs_helper.py` with the updated folder as an argument and trigger a local Plex scan of that folder.

This is useful for people who run Plex Media Server on a different server than Sonarr/Radarr/etc. It's possible to have media appear in your Plex server within 5-10 minutes of downloading using this program, along with an rclone `--cache-tmp-wait-time 5m`.

## Requirements

1. Python 3+
2. Your rclone cache mount must include `--log-level INFO`
3. Your rclone cache mount must include `--syslog` **OR** `--log-file /path/to/file.log`

## Installation

1. Clone this repo: `git clone https://github.com/stokkes/plex_rcs.git`
2. Install the requirements: `pip3 install -r requirements.txt`

## Configuration

1. Copy the `config.yml.default` to `config.yml`
2. Edit `config.yml` to include your [X-Plex-Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/), set your `media_root` setting and any other settings. _See below for more information on the `media_root` setting_.

## Running plex_rcs

There are two ways I recommend you run this. Using `screen` or using the included `plex_rcs.service` systemd service _(coming soon)_.

### Using `screen`

Execute the program using screen:

`/usr/bin/screen -dmS plexrcs /path/to/plex_rcs/plex_rcs.sh`

To view the console: `screen -r plexrcs`

### Using systemd

_**Coming soon**_

1. Edit the included `plex_rcs.service` file and change the path to where the `plex_rcs.sh` file is located
2. Copy the systemd file to `/etc/systemd/service`: `sudo cp plex_rcs.service /etc/systemd/service`
3. Reload systemd: `sudo systemctl daemon-reload`
4. Enable the service [auto-starts on boot]: `sudo systemctl enable plex_rcs`
5. Start the service: `sudo systemctl start plex_rcs`

## More info on `media_root` configuration setting

This setting may be tricky to figure out at the first glance, but it is critical to get `plex_rcs` working properly. 

The value of this setting is the folder **inside your docker container** (if using docker) that contains all your media. Typically, this would be in `/media`. If not using docker, this will likely be the path to your rclone `cache` remote mount, i.e.: `/mnt/media`

However, at this time there is 1 requirement:

The root of your rclone `cache` remote (i.e.: `gdrive-cache:`) **must** contain all your media in sub-folders, so that the remote and the folder that is mounted inside your docker container/on your system both contain the same sub-folders.

**How to test:**

1. `rclone lsd cache:` and
2. `docker exec -ti plex ls /media` (where `/media` is where your media is located inside your docker container)
3. If not using docker, `ls /path/to/rclone/cache/mount`

If the result of these two folders yield the same sub-folders, then `plex_rcs` will work correctly.

**What won't work**

1. `rclone lsd cache:` shows many different folders, not just media sub-folders
2. You've mounted the `cache:` remote to `/mnt/media` using something like `rclone mount cache:Media /mnt/media`
2. `docker exec -ti plex ls /media` shows only your media sub-folders

I hope to build some logic to help figure this out, but don't hold your breath.

## Testing

You can test `plex_rcs` if you use the built in /var/log/syslog monitoring by executing the following command (replace `tvshows` and the series/episode by your values):

`logger "Apr 21 07:20:51 plex rclone[21009]: tvshows/Survivor/Season 20/Survivor - S20E01 - Episode.mkv: received cache expiry notification"`

If you're monitoring the `plex_rcs` console, you should see activity:

```
Starting to monitor /var/log/syslog with pattern for rclone                                                                
Match found (tvshows/Survivor/Season 20/Survivor - S20E01 - Episode.mkv)!                                                  
Processing section 1, folder: /media/tvshows/Survivor/Season 20                                                              
GUI: Scanning Survivor/Season 20
```

## TODO

* Support Plexdrive (analyis required)
* Smarter logic to detect rclone cache root/docker media root
* Logging to file 