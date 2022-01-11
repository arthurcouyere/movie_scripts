#!/usr/bin/env python
import os
import re
import sys
import glob
import argparse
# import configparser
import logging
from datetime import datetime
import subprocess
from termcolor import colored

############################
# configuration
############################

default_movie_extensions = [ "mkv", "mp4", "avi" ]
default_languages_to_keep = [ "eng", "fre" ]

# configFile = "replay_data.ini"

############################
# functions
############################

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

        if len(args.lang) == 0:
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
            logging.debug("%s" % filepath)
            filepath_without_ext = os.path.splitext(filepath)[0]

            print(colored(f"# found {filepath}", "yellow"))

            output_file = filepath_without_ext + ".mux.mkv"
            languages_list = ",".join(args.lang)

            command = [ "mkvmerge", "-o", f"{filepath_without_ext}.MUX.mkv", "--audio-tracks", languages_list, "--subtitle-tracks", languages_list, filepath ]
            print(f"generating {output_file}")
            logging.debug(f"executing command: {command}")
            p = subprocess.run(command, check=True, stdout=sys.stdout, stderr=sys.stderr)
        
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
