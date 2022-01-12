#!/usr/bin/env python
import os
import re
import sys
import glob
import argparse
# import configparser
import logging
from datetime import datetime
from termcolor import colored
# from ffprobe import FFProbe
import subprocess
import json

############################
# configuration
############################

default_movie_extensions = [ "mkv", "mp4", "avi" ]
default_languages_to_keep = [ "eng", "fre" ]
ffprobe_stream_types = {
    "audio": "a",
    "subtitles": "s"
}

# configFile = "replay_data.ini"

############################
# functions
############################

def ffprobe_get_stream_languages(filename: str, stream_type: str):
    stream_language_list = None

    cmd = ["ffprobe", filename, "-select_streams", ffprobe_stream_types[stream_type], "-show_entries", "stream_tags=language", "-of", "json", "-v", "quiet"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=os.getcwd())
    proc_output = proc.stdout.read()
    
    ret = json.loads(proc_output)

    if "streams" in ret.keys():
        stream_language_list= []

        for stream in ret["streams"]:
            if "tags" in stream and "language" in stream["tags"]:
                stream_language_list.append(stream["tags"]["language"])

    return stream_language_list


def ffprobe(filename: str):
    stream_language_list = {}

    for stream_type in ["audio", "subtitles"]:
        substream_list =  ffprobe_get_stream_languages(filename, stream_type)
        if substream_list:
            stream_language_list[stream_type] = substream_list

    return stream_language_list

############################
# main
############################
if __name__ == '__main__':
    try:

        script_name = os.path.basename(__file__)

        # options
        parser = argparse.ArgumentParser(description='mkv merge subtitles')
        parser.add_argument('extensions', nargs="*", help='movie file extensions')
        parser.add_argument('-g', '--lang',      metavar='lang',      type=str,  help='languages to keep (default=%s)' % default_languages_to_keep)
        parser.add_argument('-r', '--recursive', dest='recursive',action='store_true', help='recurse in sub folders')
        parser.add_argument('-l', '--log',       dest='log',      action='store_true', help='log to file')
        parser.add_argument('-v', '--verbose',   dest='verbose',  action='store_true', help='verbose mode')

        args = parser.parse_args()
        if len(args.extensions) == 0:
            args.extensions = default_movie_extensions

        if args.lang == None or len(args.lang) == 0:
            args.lang = default_languages_to_keep

        # logger
        if args.verbose:
            logLevel = logging.DEBUG
        else:
            logLevel = logging.INFO            
        logging.basicConfig(stream=sys.stdout, level=logLevel, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger()

        if args.log:
            logFile = "%s_%s.log" % (script_name, datetime.now().strftime('%Y%m%d_%H%M%S'))
            fileHandler = logging.FileHandler(logFile)
            fileHandler.setLevel(logging.INFO)
            fileHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(fileHandler)

        file_list = []
        for movie_extension in args.extensions:
            file_pattern = "*.%s"  % movie_extension
            if args.recursive:
                file_pattern = "**/%s" % file_pattern

            file_list += glob.glob(file_pattern, recursive=args.recursive)

        for filepath in sorted(file_list):

            # Local file
            print(colored(filepath, "yellow"))
            stream_list = ffprobe(filepath)
            if stream_list:
                for (stream_type, language_list) in stream_list.items():
                    language_list_str = ", ".join([colored(l, "cyan") for l in language_list])
                    print("{:10}: {}".format(stream_type, language_list_str))

        
    # catch keyboard interrupt or broken pipe
    except (KeyboardInterrupt) as e:
        print("\ninterrupted")
        try:
            sys.stdout.close()
        except IOError:
            pass
        try:
            sys.stderr.close()
        except IOError:
            pass
