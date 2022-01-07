#!/usr/bin/env python

# from justwatch import JustWatch
import os
import re
import sys
import glob
import argparse
import logging
# import logging.config
# import datetime
import requests
import json
from fuzzywuzzy import fuzz
from termcolor import colored

############################
# configuration
############################

default_movie_extensions = [ "mkv", "mp4", "avi" ]
min_fuzz_ratio = 70
default_content_type_list = ["show", "movie"]
monetization_type_list = ["flatrate", "free"]
default_provider_list = ["nfx", "prv", "dnp"]
provider_names = {
    "nfx": "Netflix",
    "prv": "Amazon Prime Video",
    "dnp": "Disney Plus",
    "slt": "Salto",
    "itu": "Apple iTunes",
    "ply": "Google Play Movies",
    "yot": "YouTube",
    "amz": "Amazon Videos",
}

############################
# classes
############################

class Content():
    title = None
    release_year = None
    ratio = None
    provider_list = []

    def __init__(self, 
        title: str,
        ratio: int,
        release_year: int = None,
        provider_list: list = None
    ):
        self.title = title
        self.ratio = ratio
        if release_year != None:
            self.release_year = release_year 
        if provider_list != None:
            self.provider_list = provider_list

    def __str__(self) -> str:
        providers = [ provider_names[p] for p in self.provider_list]
        return "%s (%s) [ratio: %s] -> %s" % (self.title, self.release_year, self.ratio, ", ".join(providers))

############################
# functions
############################

def get_title_year_from_filename(filename: str) -> tuple:
    title = filename
    year = None

    filename = re.sub(r"[\(\)\.]", " ", filename)
    filename = re.sub(" +", " ", filename)
    filename = re.sub(" *(the)* *movie", " ", filename, flags=re.IGNORECASE)

    m = re.match("(.+) ([0-9]{4}) ", filename)
    if m:
        title = m.group(1)
        title = title.replace(".", " ")
        year = int(m.group(2))

    return (title, year)

def search_content(query: str, content_type_list: list = default_content_type_list) -> list:

        body = {
            "query": query,
            "content_types": content_type_list,
            "monetization_types": monetization_type_list,
            "providers": default_provider_list,
            "enable_provider_filter": True,
            "matching_offers_only": True,
            "is_upcoming": False,
            "page": 1,
            "page_size": 5,
        }

        payload = {
            "language": "en",
            "body": json.dumps(body)
        }

        # print(payload)

        url = 'https://apis.justwatch.com/content/titles/fr_FR/popular'
        r = requests.get(url, params=payload)

        if r.status_code != 200:
            raise Exception(f"ERROR {r.status_code}: {r.content}")
        
        results = r.json()
        search_result_list = results["items"]
        content_list = []
        
        for search_result in search_result_list:
            
            ratio = fuzz.ratio(search_result["title"], query.lower())            
            if ratio > min_fuzz_ratio:

                provider_list = []
                for offer in search_result["offers"]:
                    if offer["monetization_type"] in monetization_type_list \
                        and offer["package_short_name"] in default_provider_list \
                        and offer["package_short_name"] not in provider_list :
                        provider_list.append(offer["package_short_name"])
                
                content = Content(
                    title = search_result["title"],
                    ratio = ratio,
                    release_year = search_result["original_release_year"],
                    provider_list = provider_list
                )

                content_list.append(content)

        return content_list
            
############################
# main
############################
if __name__ == '__main__':
    try:

        script_name = os.path.basename(__file__)

        # options
        parser = argparse.ArgumentParser(description='automatic providers search')
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
        # logger = logging.getLogger()

        # if args.log:
        #     logFile = "%s_%s.log" % (script_name, datetime.now().strftime('%Y%m%d_%H%M%S'))
        #     fileHandler = logging.FileHandler(logFile)
        #     fileHandler.setLevel(logging.INFO)
        #     fileHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        #     logger.addHandler(fileHandler)

        for movie_extension in args.extensions:
            
            file_pattern = "*.%s"  % movie_extension
            if args.recursive:
                file_pattern = "**/%s" % file_pattern

            for filepath in sorted(glob.glob(file_pattern, recursive=args.recursive)):
                logging.debug("%s" % filepath)
                filepath_without_ext = os.path.splitext(filepath)[0]

                (title, year) = get_title_year_from_filename(filepath_without_ext)
                logging.debug("title: [%s] year: %s" % (title, year))

                content_list = search_content(query = title, content_type_list = ["movie"])

                for content in content_list:
                    logging.debug("found: %s" % str(content))
                    if len(content.provider_list) > 0:
                        print("%s:" % (filepath))

                        if (year != None) and (year == content.release_year):
                            color = "green"
                        else:
                            color = "yellow"

                        print(colored("\t" + str(content), color))
                
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
