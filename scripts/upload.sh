#!/bin/sh

# Upload & delete mp3 files from stash ;)
find $1 -name "*mp3" -exec ftp-upload -u $ftp_user --password $ftp_pass -h $ftp_host -d data {} \; -exec rm {} \;

