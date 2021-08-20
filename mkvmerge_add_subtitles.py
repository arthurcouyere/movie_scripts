#!/usr/bin/env python
import os
import re
import sys
import glob
import argparse
# import configparser
import logging
import logging.config
import subprocess
from termcolor import colored

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
        parser = argparse.ArgumentParser(description='mkv merge subtitles')
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

        for movie_extension in args.extensions:
            
            file_pattern = "*.%s"  % movie_extension
            if args.recursive:
                file_pattern = "**/%s" % file_pattern

            for filepath in glob.glob(file_pattern, recursive=args.recursive):
                logging.debug("%s" % filepath)
                filepath_without_ext = os.path.splitext(filepath)[0]

                subtitle_list = {}

                for subtitle_extension in default_subtitle_extensions:
                    subtitle_file_pattern = "%s.*.%s" % (filepath_without_ext, subtitle_extension)
                    for subtitle_filepath in glob.glob(subtitle_file_pattern):
                        m = re.match("%s.([a-z]{2,3}).%s" % (filepath_without_ext, subtitle_extension), subtitle_filepath)
                        if (m):
                            lang = m.group(1)
                            logging.debug("subtitle found : %s (lang=%s)" % (subtitle_filepath, lang))
                            subtitle_list[lang] = subtitle_filepath

                if len(subtitle_list) > 0:
                    print(colored(f"# found {filepath}", "yellow"))

                    output_file = filepath_without_ext + ".mux.mkv"

                    command = [ "mkvmerge", "-o", f"{filepath_without_ext}.MUX.mkv", filepath ]
                    for (lang, subtitle_filepath) in subtitle_list.items():
                        command += [ "--language", f"0:{lang}", subtitle_filepath ]
                        print(f"found subtitle {subtitle_filepath} (lang: {lang})")

                    print(f"generating {output_file}")
                    logging.debug(f"executing command: {command}")
                    p = subprocess.run(command, check=True, stdout=sys.stdout, stderr=sys.stderr)
        
    # catch keyborad interrupt or broken pipe
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
