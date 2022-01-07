#!/bin/bash

# wrapper for OpenSubtitlesDownload.py
find . -maxdepth 1 \( -name "*.mp4" -o -name "*.mkv" \) -a -not -name "*.MUX.*" -print0 | while read -d $'\0' file
do
    OpenSubtitlesDownload.py "$file"
done