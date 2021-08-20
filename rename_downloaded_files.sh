#!/bin/bash

file_list=$(find -type f | egrep "\/[a-zA-Z0-9]+\.(mp4|mkv|avi)")

if [ -z "$file_list" ]; then
    echo "no files found"
    exit
fi

echo "$file_list"
read -p "Do you wish to rename these files? [y/N] " answer
if [ "$answer" == "${answer#[Yy]}" ]; then
    echo "canceled"
    exit
fi

for file in $file_list; do

    # moving and renaming file
    ext="${file##*.}"
    dir=$(dirname $file)
    new_file="$dir.$ext"
    echo "$file -> $new_file"
    mv "$file" "$new_file"

    # find optional subtitle files
    subtitle_file_list=$(find $dir -type f | egrep "\.(sfv|srt)$")
    if [ ! -z "$subtitle_file_list" ]; then
        for subtitle_file in $subtitle_file_list; do
            subtitle_ext="${subtitle_file##*.}"
            new_subtitle_file="$dir.$subtitle_ext"
            echo "$subtitle_file -> $new_subtitle_file"
            mv "$subtitle_file" "$new_subtitle_file"
        done
    fi

    # delete folder if empty
    if [ -z "$(ls -A $dir)" ]; then
        rmdir $dir
    fi    
done
