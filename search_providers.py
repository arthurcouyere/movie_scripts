#!/usr/bin/env python

import os
import re
import sys
import glob
import argparse
import logging
from datetime import datetime
import requests
import json
from fuzzywuzzy import fuzz
from termcolor import colored
from tqdm import tqdm

############################
# configuration
############################

search_url = "https://apis.justwatch.com/content/titles/fr_FR/popular"
default_language = "fr"
default_movie_extensions = [ "mkv", "mp4", "avi" ]
default_min_fuzz_ratio = 70
default_content_type_list = ["movie"]
default_monetization_type_list = ["flatrate", "free"]
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
    type = None
    release_year = None
    ratio = None
    provider_list = []

    def __init__(self, 
        title: str,
        type: str,
        ratio: int,
        release_year: int = None,
        provider_list: list = None
    ):
        self.title = title
        self.type = type
        self.ratio = ratio
        if release_year != None:
            self.release_year = release_year 
        if provider_list != None:
            self.provider_list = provider_list

    def __str__(self) -> str:
        providers = [ provider_names[p] for p in self.provider_list]
        return "%s (%s) [%s] [ratio: %s] -> %s" % (self.title, self.release_year, self.type, self.ratio, ", ".join(providers))

############################
# functions
############################

def get_title_year_from_filename(filename: str) -> tuple:
    filename = os.path.basename(filename)

    # default values
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

def search_content(query: str, language: str = None, content_type_list: list = None, min_fuzz_ratio: int = None) -> list:

    if language == None:
        language = default_language

    if content_type_list == None:
        content_type_list = default_content_type_list

    if min_fuzz_ratio == None :
        min_fuzz_ratio = default_min_fuzz_ratio

    body = {
        "query": query,
        "content_types": content_type_list,
        "monetization_types": default_monetization_type_list,
        "providers": default_provider_list,
        "enable_provider_filter": True,
        "matching_offers_only": True,
        "is_upcoming": False,
        "page": 1,
        "page_size": 5,
    }

    payload = {
        "language": language,
        "body": json.dumps(body)
    }

    r = requests.get(search_url, params=payload)

    if r.status_code != 200:
        raise Exception(f"ERROR {r.status_code}: {r.content}")
    
    results = r.json()
    search_result_list = results["items"]
    content_list = []
    
    for search_result in search_result_list:
             
        logging.debug("search result : %s (%s) [%s]" % (search_result["title"], search_result["original_release_year"], search_result["object_type"]))

        ratio = fuzz.ratio(search_result["title"], query.lower())
        logging.debug("fuzz ratio=%s" % ratio)
        if ratio >= min_fuzz_ratio:
            logging.debug("[content found] ratio of %s >= %s" % (ratio, min_fuzz_ratio))

            provider_list = []
            for offer in search_result["offers"]:
                if offer["monetization_type"] in default_monetization_type_list \
                    and offer["package_short_name"] in default_provider_list \
                    and offer["package_short_name"] not in provider_list :
                    provider = offer["package_short_name"]
                    provider_list.append(provider)
                    logging.debug("[provider] %s" % provider)
            
            content = Content(
                title = search_result["title"],
                ratio = ratio,
                type = search_result["object_type"],
                release_year = search_result["original_release_year"],
                provider_list = provider_list
            )

            content_list.append(content)
        else:
            logging.debug("[skipped] ratio of %s < %s" % (ratio, min_fuzz_ratio))

    return content_list
            
############################
# main
############################
if __name__ == '__main__':
    try:

        script_name = os.path.basename(__file__)

        # options
        parser = argparse.ArgumentParser(description='automatic providers search')
        parser.add_argument('extensions', nargs="*", help='movie file extensions (default=%s)' % str(default_movie_extensions))
        parser.add_argument('-m', '--min-ratio',  metavar='min_ratio', type=int,  help='minimun fuzz radio (default=%s)' % default_min_fuzz_ratio)
        parser.add_argument('-g', '--lang',       metavar='lang',      type=str,  help='language for search (default=%s)' % default_language)
        parser.add_argument('-t', '--types',      metavar='types',     nargs="+", help='content types for search : movie, show (default=%s)' % str(default_content_type_list))
        parser.add_argument('-y', '--year-match', dest='year_match', action='store_true', help='display only content matching year')
        parser.add_argument('-a', '--all',        dest='all',        action='store_true', help='display all files, even if no content found')
        parser.add_argument('-r', '--recursive',  dest='recursive',  action='store_true', help='recurse in sub folders')
        parser.add_argument('-l', '--log',        dest='log',        action='store_true', help='log to file')
        parser.add_argument('-v', '--verbose',    dest='verbose',    action='store_true', help='verbose mode')

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

        for filepath in tqdm(sorted(file_list)):
            logging.debug("%s" % filepath)
            filepath_without_ext = os.path.splitext(filepath)[0]

            (title, year) = get_title_year_from_filename(filepath_without_ext)
            logging.debug("title: [%s] year: %s" % (title, year))

            content_list = search_content(query = title, language= args.lang, content_type_list = args.types, min_fuzz_ratio = args.min_ratio)

            output = ""

            for content in content_list:
                logging.debug("found: %s" % str(content))
                if len(content.provider_list) > 0:
                    
                    year_matches = False
                    if year == None:
                        color = "cyan"
                    elif year == content.release_year:
                        year_matches = True
                        color = "green"
                    else:
                        color = "yellow"
                    
                    if year_matches or not args.year_match:
                        output += colored("\t" + str(content) + "\n", color)

            if output or args.all:
                tqdm.write(filepath)
                tqdm.write(output, end="")
                # content_found = True
                
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
