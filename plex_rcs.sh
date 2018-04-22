#!/bin/bash

#Set Script Name variable
SCRIPT=`basename ${BASH_SOURCE[0]}`

# Confirm if config.yml exists
if [ ! -f "$(dirname $0)/config.yml" ]; then
	echo "$(dirname $0)/config.yml not found. Have you configured your settings?"
	exit 1;
fi

#Initialize variables to default values.
LOG_FILE="/var/log/syslog"
SYSTEM="rclone"

#Set fonts for Help.
NORM=`tput sgr0`
BOLD=`tput bold`
REV=`tput smso`

#Help function
function HELP {
  echo -e "${REV}Basic usage:${NORM} ${BOLD}$SCRIPT${NORM}"\\n
  echo "Command line switches are optional. The following switches are recognized."
  echo "${REV}-f${NORM}  --File to monitor. Default is ${BOLD}/var/log/syslog${NORM}."
  echo "${REV}-s${NORM}  --System to use (rclone/plexdrive). Default is ${BOLD}rclone${NORM}."
  echo -e "${REV}-h${NORM}  --Displays this help message."\\n
  echo -e "Example: ${BOLD}$SCRIPT -f /home/user/rclone.log -s rclone${NORM}"\\n
  exit 1
}

### Start getopts code ###

while getopts :f:s:h FLAG; do
  case $FLAG in
    f)  #set LOG_FILE
      LOG_FILE=$OPTARG
	  if [ ! -f $LOG_FILE ]; then
	  	echo "$LOG_FILE does not exist, exitiing."
	  	exit 1
	  fi
      ;;
    s)  #set system to use (rclone/plexdrive)
      SYSTEM=$OPTARG
      if [ $SYSTEM != "rclone" || $SYSTEM != "plexdrive" ]; then
      	echo "$SYSTEM is invalid. It must be 'rclone' or 'plexdrive', exiting."
        exit 1
      fi
      ;;
    h)  #show help
      HELP
      ;;
    \?) #unrecognized option - show help
      echo -e \\n"Option -${BOLD}$OPTARG${NORM} not allowed."
      HELP
      ;;
  esac
done

shift $((OPTIND-1))  #This tells getopts to move on to the next argument.

### End getopts code ###


### Main loop to process files ###

if [ $SYSTEM == "rclone" ]; then
	PATTERN_MATCH="(mkv:|mp4:|mpeg4:|avi:) received cache expiry notification"
	PATTERN_REPLACE="s/.*rclone\[[0-9]\+\]: \([^:]*\).*$/\1/g"
else
	PATTERN_MATCH = "(mkv:|mp4:|mpeg4:|avi:) received cache expiry notification"
	PATTERN_REPLACE = "'s/.*rclone\[[0-9]\+\]: \([^:]*\).*$/\1/g'"
fi

# Write to log file that we're starting to monitor
logger "Started real-time monitoring of syslog for new media via rclone cach expiration notifications."

echo "Starting to monitor $LOG_FILE with pattern for $SYSTEM"
	
# The magic
tail -Fn0 $LOG_FILE | \
while read line ; do
        egrep -q "$PATTERN_MATCH" <<< $line
        if [ $? = 0 ]
        then        	
        	file=$(sed "$PATTERN_REPLACE" <<< $line)
			folder=$(dirname "$file")
			# Calls helper python script
			echo "Match found ($file)!"
			$(dirname $0)/plex_rcs_helper.py -d "$folder"
        fi
done