#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 python36Packages.requests python36Packages.lxml
#
# To run an interactive shell:
#  $ nix-shell -p python36 python36Packages.lxml python36Packages.requests --run "python3 -i converter.py"

import os
import re
import urllib.parse
import requests
import json
import time
import lxml.html as LH

from collections import namedtuple
from lxml import etree

from typing import *

baseUrl: str = "https://demeter.dtek.se/wiki/"

class Revision(NamedTuple):
    diff: int
    author: str
    comment: str
    content: Optional[str]

    def has_content(self) -> bool:
        return self.content is not None


def set_content(r: Revision, content: str) -> Revision:
    """Returns a new Revision with updated content"""
    return Revision(r.diff, r.author, r.comment, content)

# Type aliases
Session = requests.sessions.Session
Response = requests.Response
FilePath = str

def findDiffMarkup(session: Session, page: FilePath, diff: str) -> Optional[str]:
    """
    Extracts the HTML of the revision by requesting the PmWiki instance
    to render a preview of said revision
    """
    print(page, diff)
    pageWithSlash = page.replace(".", "/")
    response = session.get(baseUrl + pageWithSlash + "?action=edit&restore=diff:"+diff+":"+diff+"&preview=y")

    tree = LH.fromstring(response.content)
    basetime = tree.xpath('//input[@name="basetime"]')
    content = tree.xpath('//textarea[@id="text"]/text()')

    if len(basetime) == 0:
        print("Invalid", page, diff)
        return None

    if len(content) == 0:
        return None

    data = {
        'action':'edit',
        'n':page,
        'basetime':basetime[0].value,
        'text':content[0],
        'csum':'',
        'author':'simonwi',
        'preview':'+Förhandsgranska+'
    }

    response = session.post(baseUrl + page + "?action=edit", data, session.headers)
    return extractHtml(response)

def extractHtml(response: Response) -> str:
    """Extracts the html inside the 'wikitext'-div"""
    elements = LH.fromstring(response.content).xpath('//div[@id="wikitext"]')[0].getchildren()
    return "\n".join(str(etree.tostring(el, encoding='unicode', method='html', pretty_print=True)) for el in elements)

def findRevisionsMeta(file: FilePath) -> Tuple[str, List[Revision]]:
    """Finds the metadata about revisions for a page"""
    with open(file, 'r') as f:
        fileText = f.read()
        match = re.search('(?:name=)(.*)', fileText)

        name = match.group(1)
        regex = re.compile('author:(?P<diff>\d{10})=(?P<author>[\w\/]*)\s(?:csum:\d{10}=(?P<comment>.*))?', re.MULTILINE)
        revisions = []

        for matches in re.finditer(regex, fileText):
            revisions.append(Revision(int(matches.group('diff')), matches.group('author'),
                                      matches.group('comment'), None))

        return name, revisions

def findRevisions(session: Session, file: FilePath) -> List[Revision]:
    """Return the revisions for a page"""
    name, revisions = findRevisionsMeta(file)

    return list(set_content(r, findDiffMarkup(session, name, str(r.diff))) for r in revisions)

def findAndConvertPages(session: Session, directory: FilePath, namespaces: List[str],
                        ignored_names: List[str], offset = 0) -> None:
    """
    Creates converted copies of PmWiki page-files in converted/ directory.

    The converted files will be in a serialized JSON format:
    { 'diff': int, 'author': str, 'comment': str, 'content': html }


    Where 'diff' is some kind of timestamp, 'author' is a user account on
    the PmWiki instance, 'comment' is just an ordinary string and 'content'
    is a python string representation of the html of that revision.

    Only pages within the specified namespaces will be converted and that are not
    in the skipped_names-list (without namespace).
    """

    # Create directory structure
    if not os.path.exists("converted"):
        os.mkdir("converted")
        for ns in namespaces:
            if not os.path.exists(f"converted/{ns}"):
                os.mkdir(f"converted/{ns}")

    def page_predicate(page: str) -> bool:
        """Simple predicate for removing unwanted pages"""
        parts = page.split(".", 1)
        return ("," not in page) and (parts[0] in namespaces) and (parts[1] not in ignored_names)


    pages = (page.split(".", 1) for page in sorted(os.listdir(directory)[offset:]) if page_predicate(page))

    for (page_ns, page_name) in pages:
        if not os.path.isfile(f"converted/{page_ns}/{page_name}"):
            with open(f'converted/{page_ns}/{page_name}', 'w') as f:
                f.write(json.dumps(findRevisions(session, directory+page_ns+"."+page_name),
                                   sort_keys=True, indent=4, separators=(',', ': ')))

        # if the file already exists we assume it has been converted already
        else:
            print(f"converted/{page_ns}/{page_name} is already parsed, if it is not finished, remove this file.")

def main(filename: str, username: str, password: str) -> None:
    with requests.Session() as s:
        s.post(baseUrl + "Main/LoginPage?action=login" ,
               data={"username": username,"password": password})
        findAndConvertPages(s, "/home/jassob/Projects/pm-wiki-exporter/wiki.d/",
                            ["Main", "Profiles"], ["RecentChanges", "GroupAttributes", "Profiles"])

main("", "simonwi", "hackehackspett")
