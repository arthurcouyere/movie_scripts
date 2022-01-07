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
# import autosubsync
import ffsubsync

############################
# configuration
############################

default_movie_extensions = [ "mkv", "mp4", "avi" ]
default_subtitle_extensions = [ "ass", "srt" ]

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
        parser = argparse.ArgumentParser(description='automatic subtitles sync')
        parser.add_argument('extensions', nargs="*", help='movie file extensions')
        parser.add_argument('-r', '--recursive', dest='recursive',action='store_true', help='recurse in sub folders')
        parser.add_argument('-l', '--log',       dest='log',      action='store_true', help='log to file')
        parser.add_argument('-v', '--verbose',   dest='verbose',  action='store_true', help='verbose mode')

        args = parser.parse_args()
        if len(args.extensions) == 0:
            args.extensions = default_movie_extensions

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

            subtitle_list = {}

            for subtitle_extension in default_subtitle_extensions:
                subtitle_file_pattern = "%s.*.%s" % (glob.escape(filepath_without_ext), subtitle_extension)
                for subtitle_filepath in glob.glob(subtitle_file_pattern):
                    logging.debug("found file: %s" % subtitle_filepath)
                    m = re.match(r"%s.([a-z]{2,3}).%s" % (re.escape(filepath_without_ext), subtitle_extension), subtitle_filepath)
                    if (m):
                        lang = m.group(1)
                        logging.debug("subtitle found : %s (lang=%s)" % (subtitle_filepath, lang))
                        subtitle_list[lang] = subtitle_filepath

            if len(subtitle_list) > 0:
                output_file = filepath_without_ext + ".mux.mkv"

                for (lang, subtitle_filepath) in subtitle_list.items():
                    (subtitle_filepath_without_ext, subtitle_extension) = os.path.splitext(subtitle_filepath)
                    subtitle_output_file = subtitle_filepath_without_ext + ".synced" + subtitle_extension

                    print(colored(f"# syncing {subtitle_filepath}", "yellow"))

                    # autosubsync.synchronize(filepath, subtitle_filepath, subtitle_output_file)
                    command = [ "ffs", filepath, "-i", subtitle_filepath, "-o", subtitle_output_file ]
                    logging.debug(f"executing command: {command}")
                    p = subprocess.run(command, check=True, stdout=sys.stdout, stderr=sys.stderr)                        
                    if (os.path.exists(subtitle_output_file)):
                        os.rename(subtitle_filepath, subtitle_filepath + ".old")
                        os.rename(subtitle_output_file, subtitle_filepath)

        
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
